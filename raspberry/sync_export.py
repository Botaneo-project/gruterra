"""Bounded SQLite outbox over authenticated SSH; never deletes readings."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

TABLES = {'current': 'measurements', 'history': 'history_measurements'}


def payload(row, kind):
    item = dict(row)
    item.pop('sync_state', None)
    item.pop('confirmed_at', None)
    item['kind'] = kind
    return item


def digest(item):
    return hashlib.sha256(json.dumps(item, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def export(db, device):
    rows = []
    for kind, table in TABLES.items():
        rows.extend(payload(r, kind) for r in db.execute(
            f"SELECT * FROM {table} WHERE sync_state='pending' ORDER BY rowid LIMIT ?", (500-len(rows),)))
    pending = sum(db.execute(f"SELECT COUNT(*) FROM {t} WHERE sync_state='pending'").fetchone()[0] for t in TABLES.values())
    return {'version': 1, 'device_id': device, 'rows': rows, 'pending': pending}


def collect_now(base, request):
    """Queue the existing collector; never open a second Bluetooth reader."""
    if not isinstance(request, dict):
        raise ValueError('Invalid collection request')
    # The existing collector reads all configured sensors, just like the mobile button.
    data = base / 'data'
    state = json.loads((data/'collect-state.json').read_text())
    if state.get('running'):
        return {'accepted': False, 'status': 'running', 'message': 'Collecte déjà en cours. Les nouvelles mesures seront récupérées à la prochaine synchronisation.'}
    try:
        with (data/'collect.request').open('x') as stream:
            stream.write('manual')
    except FileExistsError:
        return {'accepted': False, 'status': 'pending', 'message': 'Demande de collecte déjà en attente.'}
    return {'accepted': True, 'status': 'pending', 'message': 'Collecte demandée pour les capteurs du Raspberry. Les nouvelles mesures seront récupérées à la prochaine synchronisation.'}


def acknowledge(db, device, request):
    if request['device_id'] != device or len(request['rows']) > 500:
        raise ValueError('Invalid acknowledgement')
    with db:
        for item in request['rows']:
            table = TABLES[item['kind']]
            row = db.execute(f'SELECT * FROM {table} WHERE measurement_id=? AND device_id=?',
                             (item['measurement_id'], device)).fetchone()
            if row is None or digest(payload(row, item['kind'])) != item['digest']:
                raise ValueError('Acknowledgement mismatch')
            db.execute(f"UPDATE {table} SET sync_state='confirmed' WHERE measurement_id=?", (item['measurement_id'],))
    return {'confirmed': len(request['rows'])}


if __name__ == '__main__':
    base = Path.home() / 'botaneo'
    device = json.loads((base/'config/collector.json').read_text())['device_id']
    db = sqlite3.connect((base/'data/collector.sqlite3').as_uri()+'?mode=rw', uri=True, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA synchronous=FULL')
    try:
        if sys.argv[1:] == ['export']:
            result = export(db, device)
        elif sys.argv[1:] == ['collect_now']:
            result = collect_now(base, json.loads(sys.stdin.read(250001)))
        elif sys.argv[1:] == ['ack']:
            result = acknowledge(db, device, json.loads(sys.stdin.read(250001)))
        else:
            raise ValueError('Unknown operation')
        print(json.dumps(result))
    finally:
        db.close()
