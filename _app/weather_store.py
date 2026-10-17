"""Import local météo en préparation : aucun réseau ni activation automatique."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from weather_protocol import validate_batch, canonical, PROTOCOL

def import_batch(path,batch,device_id):
    validate_batch(batch,device_id)
    counts={'added':0,'duplicates':0,'revisions':0}
    with closing(sqlite3.connect(Path(path))) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute('CREATE TABLE IF NOT EXISTS weather_observations_v1 (observation_id TEXT NOT NULL, revision_hash TEXT NOT NULL, observation_json TEXT NOT NULL, retrieved_at TEXT NOT NULL, PRIMARY KEY(observation_id,revision_hash))')
            db.execute('CREATE TABLE IF NOT EXISTS weather_receipts_v1 (device_id TEXT NOT NULL, observation_id TEXT NOT NULL, revision_hash TEXT NOT NULL, PRIMARY KEY(device_id,observation_id,revision_hash))')
            for row in batch['rows']:
                pair=(row['observation_id'],row['revision_hash'])
                content=canonical(row['observation']).decode('utf-8')
                previous=db.execute('SELECT observation_json FROM weather_observations_v1 WHERE observation_id=? AND revision_hash=?',pair).fetchone()
                if previous:
                    if previous[0]!=content:raise ValueError('weather_hash_content_conflict')
                    counts['duplicates']+=1
                else:
                    revised=db.execute('SELECT 1 FROM weather_observations_v1 WHERE observation_id=? LIMIT 1',(pair[0],)).fetchone()
                    db.execute('INSERT INTO weather_observations_v1 VALUES (?,?,?,?)',(*pair,content,row['retrieved_at']))
                    counts['added']+=1
                    counts['revisions']+=bool(revised)
                db.execute('INSERT OR IGNORE INTO weather_receipts_v1 VALUES (?,?,?)',(device_id,*pair))
            db.commit()
        except BaseException:
            db.rollback()
            raise
    # Aucune confirmation renvoyée avant commit et fermeture de la connexion.
    ack={'protocol':PROTOCOL,'protocol_version':1,'device_id':device_id,'rows':[{'observation_id':r['observation_id'],'revision_hash':r['revision_hash']} for r in batch['rows']]}
    return counts,ack

def analysis_candidates(path):
    """Sélection conservatrice, sans somme de pluie ni arbitrage de révision."""
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        rows=db.execute('SELECT observation_id,revision_hash,observation_json FROM weather_observations_v1').fetchall()
    observations={(identity,digest):json.loads(content) for identity,digest,content in rows}
    blocked=set();replaced=set();links={};children={};identities={}
    for pair,obs in observations.items():
        identities.setdefault(pair[0],[]).append(pair)
        if obs['source_time'] is None or obs['module_id'] is None or obs['value'] is None:blocked.add(pair)
        predecessor=obs['supersedes']
        if predecessor is None:continue
        old=(predecessor['observation_id'],predecessor['revision_hash'])
        parent=observations.get(old)
        comparable=('source','station_id','module_id','api_field','metric','value','unit','source_time','time_precision','temporal_quality','provenance')
        if parent is None or any(obs[key]!=parent[key] for key in comparable):
            blocked.add(pair);continue
        before,after=parent['period'],obs['period']
        # Précision seule : ne pas autoriser une modification des bornes déjà connues.
        if any(value is not None and value!='unknown' and after[key]!=value for key,value in before.items()):
            blocked.add(pair);continue
        links[pair]=old;children.setdefault(old,[]).append(pair)
    # Plusieurs versions ou descendants : aucun arbitrage fondé sur la réception.
    for versions in identities.values():
        if len(versions)>1:blocked.update(versions)
    for old,descendants in children.items():
        if len(descendants)>1:blocked.update([old,*descendants])
    for pair in links:
        seen=set();cursor=pair
        while cursor in links:
            if cursor in seen:
                blocked.update(seen);break
            seen.add(cursor);cursor=links[cursor]
        if cursor in blocked:blocked.update(seen)
    # Propager l'attente d'un prédécesseur ambigu à tous ses successeurs.
    changed=True
    while changed:
        changed=False
        for pair,old in links.items():
            if old in blocked and pair not in blocked:blocked.add(pair);changed=True
    for pair,old in links.items():
        if pair not in blocked:replaced.add(old)
    return [{'observation_id':pair[0],'revision_hash':pair[1],'observation':obs} for pair,obs in observations.items() if pair not in blocked and pair not in replaced]
