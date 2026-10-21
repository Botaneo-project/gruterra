"""Suivi privé local des opérations V2. Aucun transport ni activation du partage."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sqlite3
import uuid
from botaneo_config import CONFIG_DIR
from contribution_protocole import UUID4, ORIGIN
from contribution_donnees import valider_contribution_v2
from i18n import traduire_courant as t


def _allow():
    if os.environ.get('BOTANEO_DEMO') == '1':
        raise ValueError(t('contribution_demo_blocked'))


def chemin():
    return CONFIG_DIR / 'contribution_suivi.sqlite3'


def _uuid(value):
    if type(value) is not str or not UUID4.fullmatch(value):
        raise ValueError(t('contribution_tracking_invalid'))


def _date(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise ValueError(t('contribution_tracking_invalid'))
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(t('contribution_tracking_invalid')) from None


def _pairs(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ValueError(t('contribution_tracking_invalid'))
        result[key] = value
    return result


def _json(payload):
    try:
        return json.loads(payload.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError):
        raise ValueError(t('contribution_tracking_invalid')) from None


@contextmanager
def _db():
    _allow()
    path=chemin()
    path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path, timeout=5)
    conn.row_factory=sqlite3.Row
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY, contributor_id TEXT NOT NULL,
                operation TEXT NOT NULL, payload BLOB NOT NULL, payload_sha256 TEXT NOT NULL,
                state TEXT NOT NULL, receipt TEXT);
            CREATE INDEX IF NOT EXISTS requests_identity ON requests(contributor_id,state);
            CREATE TABLE IF NOT EXISTS withdrawal_covers (
                withdrawal_id TEXT NOT NULL REFERENCES requests(request_id),
                contribution_request_id TEXT NOT NULL REFERENCES requests(request_id),
                PRIMARY KEY(withdrawal_id,contribution_request_id));
        ''')
        conn.execute('BEGIN IMMEDIATE')
        if 'test_profile' not in {r[1] for r in conn.execute('PRAGMA table_info(requests)')}:
            conn.execute("ALTER TABLE requests ADD COLUMN test_profile TEXT NOT NULL DEFAULT 'private-test-only'")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def _request(conn, request_id):
    _uuid(request_id)
    row=conn.execute('SELECT * FROM requests WHERE request_id=?',(request_id,)).fetchone()
    if row is None:
        raise ValueError(t('contribution_tracking_invalid'))
    return row


def preparer_demande(contributor_id, operation, payload, *, profil_test='private-test-only'):
    """Valide le contenu V2 et fige les octets déjà relus.

    Le futur parcours doit présenter un aperçu avant cette fonction.
    Créer la demande ne prouve ni accord, ni envoi, ni réception.
    """
    _allow()
    if profil_test not in ('private-test-only','lifecycle-test-60s'):
        raise ValueError(t('contribution_tracking_invalid'))
    if type(contributor_id) is not str or not re.fullmatch(r'ed25519:[0-9a-f]{64}',contributor_id):
        raise ValueError(t('contribution_tracking_invalid'))
    if operation not in ('contribute','withdraw') or type(payload) is not bytes or not 0<len(payload)<=2097152:
        raise ValueError(t('contribution_tracking_invalid'))
    body=_json(payload)
    if type(body) is not dict:
        raise ValueError(t('contribution_tracking_invalid'))
    if operation=='contribute':
        valider_contribution_v2(body)
    else:
        if body.get('scope')=='all' and set(body)=={'scope'}:
            pass
        elif body.get('scope')=='contribution' and set(body)=={'scope','contribution_id'}:
            _uuid(body['contribution_id'])
        else:
            raise ValueError(t('contribution_tracking_invalid'))
    request_id=str(uuid.uuid4())
    with _db() as conn:
        conn.execute('INSERT INTO requests (request_id,contributor_id,operation,payload,payload_sha256,state,receipt,test_profile) VALUES(?,?,?,?,?,?,NULL,?)',
                     (request_id,contributor_id,operation,payload,hashlib.sha256(payload).hexdigest(),'prepared',profil_test))
    return request_id


def lire_demande(request_id):
    with _db() as conn:
        return dict(_request(conn,request_id))


def marquer_en_attente(request_id):
    """À appeler par un futur transport, jamais automatiquement au lancement."""
    with _db() as conn:
        row=_request(conn,request_id)
        if row['state'] in ('confirmed','server_expired','server_withdrawn'):
            raise ValueError(t('contribution_tracking_terminal'))
        other=conn.execute("SELECT 1 FROM requests WHERE contributor_id=? AND request_id<>? AND state IN ('pending','check')",
                           (row['contributor_id'],request_id)).fetchone()
        if other:
            raise ValueError(t('contribution_tracking_busy'))
        if row['operation']=='withdraw':
            # Photographier la couverture locale une seule fois, avant traitement.
            body=_json(row['payload'])
            candidates=conn.execute("SELECT request_id,receipt FROM requests WHERE contributor_id=? AND operation='contribute' AND state='confirmed'",
                                    (row['contributor_id'],)).fetchall()
            for candidate in candidates:
                receipt=json.loads(candidate['receipt'])
                if body['scope']=='all' or receipt['contribution_id']==body['contribution_id']:
                    conn.execute('INSERT OR IGNORE INTO withdrawal_covers VALUES(?,?)',(request_id,candidate['request_id']))
        conn.execute("UPDATE requests SET state='pending' WHERE request_id=?",(request_id,))


def _validate_receipt(row, receipt, http_status):
    if http_status not in (200,201) or type(http_status) is not int or type(receipt) is not dict:
        raise ValueError
    common={'protocol_version','mode','contributor_id','request_id','status'}
    expected=common|({'contribution_id','schema_version','payload_sha256','received_at','withdrawal_endpoint','policy_version','retention_until'}
                     if row['operation']=='contribute' else {'scope','withdrawn_count','processed_at'})
    if set(receipt)!=expected or type(receipt['protocol_version']) is not int or receipt['protocol_version']!=2:
        raise ValueError
    # Le profil public et la liaison à la politique ne sont pas encore négociés.
    if receipt['mode']!='private_test' or receipt['contributor_id']!=row['contributor_id'] or receipt['request_id']!=row['request_id']:
        raise ValueError
    if row['operation']=='contribute':
        if receipt['status']!='accepted' or type(receipt['schema_version']) is not int or receipt['schema_version']!=2 or receipt['payload_sha256']!=row['payload_sha256']:
            raise ValueError
        _uuid(receipt['contribution_id'])
        start=_date(receipt['received_at'])
        if receipt['withdrawal_endpoint']!=ORIGIN+'/v2/withdrawals' or receipt['policy_version']!=row['test_profile']:
            raise ValueError
        if receipt['retention_until'] is not None and _date(receipt['retention_until'])<=start:
            raise ValueError
        if row['test_profile']=='lifecycle-test-60s':
            if receipt['retention_until'] is None or (_date(receipt['retention_until'])-start).total_seconds()!=60:
                raise ValueError
    else:
        body=_json(row['payload'])
        if receipt['status']!='withdrawn' or receipt['scope']!=body['scope'] or type(receipt['withdrawn_count']) is not int or receipt['withdrawn_count']<0:
            raise ValueError
        if body['scope']=='contribution' and receipt['withdrawn_count']>1:
            raise ValueError
        _date(receipt['processed_at'])
    return json.dumps(receipt,sort_keys=True,ensure_ascii=False,allow_nan=False)


def enregistrer_recu(request_id, receipt, http_status):
    """Profil de test seulement. Le futur appelant doit vérifier le transport HTTPS.

    Enregistrer un objet importé arbitrairement ne constitue pas une preuve
    serveur. Pas d'import de reçu ou de transport exposé à l'utilisateur ici.
    """
    invalid=False
    with _db() as conn:
        row=_request(conn,request_id)
        if row['state'] in ('prepared','server_expired','server_withdrawn'):
            raise ValueError(t('contribution_tracking_invalid'))
        try:
            encoded=_validate_receipt(row,receipt,http_status)
            if row['receipt'] is not None and row['receipt']!=encoded:
                raise ValueError
            if row['operation']=='contribute':
                others=conn.execute("SELECT receipt FROM requests WHERE contributor_id=? AND request_id<>? AND operation='contribute' AND receipt IS NOT NULL",
                                    (row['contributor_id'],request_id)).fetchall()
                if any(json.loads(other['receipt'])['contribution_id']==receipt['contribution_id'] for other in others):
                    raise ValueError
        except (ValueError,TypeError):
            invalid=True
            if row['state']!='confirmed':
                conn.execute("UPDATE requests SET state='check' WHERE request_id=?",(request_id,))
        else:
            conn.execute("UPDATE requests SET state='confirmed',receipt=? WHERE request_id=?",(encoded,request_id))
    if invalid:
        raise ValueError(t('contribution_tracking_invalid_receipt'))


def enregistrer_fin_parcours(request_id, response, http_status):
    """Réponse du futur transport HTTPS vérifié, jamais un import utilisateur.

    Le HTTP 410 décrit la contribution active, pas toutes les sauvegardes.
    Aucun nouvel identifiant ni effacement des octets/reçus historiques.
    """
    if type(http_status) is not int or http_status!=410 or type(response) is not dict or set(response)!={'error'}:
        raise ValueError(t('contribution_tracking_invalid'))
    states={'contribution_expired':'server_expired','contribution_withdrawn':'server_withdrawn'}
    if type(response['error']) is not str or response['error'] not in states:
        raise ValueError(t('contribution_tracking_invalid'))
    state=states[response['error']]
    with _db() as conn:
        row=_request(conn,request_id)
        if row['operation']!='contribute' or row['state']=='prepared':
            raise ValueError(t('contribution_tracking_invalid'))
        if row['state'] in ('server_expired','server_withdrawn') and row['state']!=state:
            raise ValueError(t('contribution_tracking_terminal'))
        conn.execute('UPDATE requests SET state=? WHERE request_id=?',(state,request_id))



def etat_local(request_id, now=None):
    """État dérivé de l'historique local, sans consultation serveur."""
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None:
        raise ValueError(t('contribution_tracking_invalid'))
    with _db() as conn:
        row=_request(conn,request_id)
        receipt=json.loads(row['receipt']) if row['receipt'] else None
        if row['state'] in ('server_expired','server_withdrawn'):
            status=row['state']
        elif row['state']=='check':
            status='check'
        elif row['operation']=='withdraw':
            status='withdrawal_confirmed' if receipt else ('prepared' if row['state']=='prepared' else 'withdrawal_pending')
        elif conn.execute("SELECT 1 FROM withdrawal_covers c JOIN requests w ON w.request_id=c.withdrawal_id WHERE c.contribution_request_id=? AND w.state='confirmed'",(request_id,)).fetchone():
            status='withdrawn'
        elif receipt and receipt['retention_until'] is not None and _date(receipt['retention_until'])<=now:
            status='deadline_reached'
        else:
            status={'prepared':'prepared','pending':'pending','confirmed':'received'}[row['state']]
        return {'status':status,'label':t('contribution_tracking_'+status),
                'server_deletion_verified':False,'receipt':receipt,
                'test_only':True,'test_profile':row['test_profile']}


def lister_demandes():
    _allow()
    if not chemin().exists():
        return []
    with _db() as conn:
        rows=conn.execute('SELECT request_id,operation FROM requests ORDER BY rowid DESC').fetchall()
    return [{**dict(row),**etat_local(row['request_id'])} for row in rows]


def ouvrir_suivi(parent, palette=None):
    """Consultation seulement : ni envoi ni import de reçus arbitraires."""
    import tkinter as tk
    from tkinter import ttk,messagebox
    window=tk.Toplevel(parent)
    window.title(t('contribution_tracking_title'))
    window.geometry('820x460')
    window.minsize(460,300)
    from ui_palette import THEME_CLAIR, THEME_SOMBRE
    from ui_scroll_form import create, create_table
    from meteo_nappes import harmoniser
    palette = palette or (THEME_SOMBRE if parent.cget('background') == THEME_SOMBRE['BG'] else THEME_CLAIR)
    body, footer = create(window, palette)
    tk.Button(footer,text=t('close'),command=window.destroy).pack(side='right')
    tk.Label(body,text=t('contribution_tracking_notice'),wraplength=400,justify='left').pack(fill='x',padx=12,pady=8)
    tree=create_table(body,palette,columns=('operation','state','request'),height=7,padx=12,pady=8)
    for column,label,width in [('operation','contribution_tracking_operation',120),('state','contribution_tracking_state',260),('request','contribution_tracking_request',300)]:
        tree.heading(column,text=t(label));tree.column(column,width=width,stretch=False)
    try:
        rows=lister_demandes()
        for row in rows:
            tree.insert('', 'end',values=(t('contribution_tracking_'+row['operation']),row['label'],row['request_id']))
        if not rows:
            tk.Label(body,text=t('contribution_tracking_empty'),wraplength=400).pack(fill='x',padx=12)
    except (ValueError,sqlite3.Error,OSError):
        messagebox.showerror(t('contribution_title'),t('contribution_tracking_unreadable'),parent=window)
    harmoniser(window, palette)
    return window
