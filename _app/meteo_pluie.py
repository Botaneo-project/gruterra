"""Historique local des cumuls reçus, jamais additionnés entre eux."""
import math
import sqlite3
from contextlib import closing
from datetime import datetime


def enregistrer(path, resultats):
    from meteo_synthese import choisir_mesure
    lignes = []
    for categorie, resultat in resultats.items():
        if resultat.get('error') is not None:
            continue
        for station in resultat.get('data') or []:
            for cle in ('pluie_1h', 'pluie_24h'):
                info = choisir_mesure(cle, [station] if categorie == 'privees' else [],
                                      [station] if categorie == 'publiques' else [],
                                      lambda s: s.get('nom') or 'Netatmo', lambda v,u: str(v))
                valeur = info.get('valeur')
                date = info.get('date')
                if type(valeur) not in (int,float) or not math.isfinite(valeur) or valeur < 0 or not date:
                    continue
                try:
                    mesure = datetime.strptime(date, '%d/%m/%Y %H:%M').isoformat(timespec='minutes')
                except (TypeError, ValueError):
                    continue
                identifiant = station.get('id') or station.get('_id')
                if not identifiant:
                    continue  # Une source inconnue ne doit pas fusionner deux stations.
                lignes.append((categorie, str(identifiant), cle, mesure, valeur,
                               info['source'], resultat.get('date')))
    if not lignes:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS pluie (categorie TEXT, station TEXT, type TEXT, mesure TEXT, mm REAL, source TEXT, reception TEXT, PRIMARY KEY(categorie,station,type,mesure))')
        avant = db.total_changes
        db.executemany('INSERT OR IGNORE INTO pluie VALUES (?,?,?,?,?,?,?)', lignes)
        return db.total_changes - avant


def derniere_pluie(path):
    if not path.exists():
        return None
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        # Le relevé positif le plus récent prime ; à date égale, préférer le cumul court.
        return db.execute("SELECT mesure,mm,source,type FROM pluie WHERE mm>0 ORDER BY mesure DESC, CASE WHEN type='pluie_1h' THEN 0 ELSE 1 END LIMIT 1").fetchone()
