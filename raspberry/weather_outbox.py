"""Durable weather outbox. No API calls, OAuth or scheduled collection."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from weather_protocol import (PROTOCOL, MAX_BYTES, MAX_ROWS, canonical, decode,
                              pack_batch, string, validate_ack, validate_row)


def connect(path):
    db = sqlite3.connect(Path(path), timeout=20)
    db.execute('PRAGMA synchronous=FULL')
    return db


def initialize(db, device_id):
    string(device_id)
    db.execute('CREATE TABLE IF NOT EXISTS weather_identity (singleton INTEGER PRIMARY KEY CHECK(singleton=1), device_id TEXT NOT NULL)')
    db.execute('INSERT OR IGNORE INTO weather_identity VALUES (1,?)', (device_id,))
    if db.execute('SELECT device_id FROM weather_identity WHERE singleton=1').fetchone()[0] != device_id:
        raise ValueError('weather_device_mismatch')
    db.execute('''CREATE TABLE IF NOT EXISTS weather_outbox_v1 (
        sequence INTEGER PRIMARY KEY, observation_id TEXT NOT NULL,
        revision_hash TEXT NOT NULL, row_json TEXT NOT NULL,
        confirmed INTEGER NOT NULL DEFAULT 0 CHECK(confirmed IN (0,1)),
        UNIQUE(observation_id, revision_hash))''')


def enqueue(path, device_id, rows):
    """Future collector entry point: all rows committed or none."""
    rows = list(rows)
    for row in rows:
        validate_row(row)
        pack_batch([row], 1, device_id)  # Reject an unexportable row before storing it.
    with closing(connect(path)) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            initialize(db, device_id)
            added = 0
            for row in rows:
                pair = (row['observation_id'], row['revision_hash'])
                old = db.execute('SELECT row_json FROM weather_outbox_v1 WHERE observation_id=? AND revision_hash=?', pair).fetchone()
                if old:
                    if canonical(json.loads(old[0])['observation']) != canonical(row['observation']):
                        raise ValueError('weather_hash_content_conflict')
                    continue  # Preserve first retrieval and existing confirmation.
                db.execute('INSERT INTO weather_outbox_v1(observation_id,revision_hash,row_json) VALUES (?,?,?)', (*pair, canonical(row).decode('utf-8')))
                added += 1
            db.commit()
            return added
        except BaseException:
            db.rollback()
            raise


def export_batch(path, device_id, max_bytes=MAX_BYTES):
    with closing(connect(path)) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            initialize(db, device_id)
            pending = db.execute('SELECT count(*) FROM weather_outbox_v1 WHERE confirmed=0').fetchone()[0]
            rows = [json.loads(row[0]) for row in db.execute('SELECT row_json FROM weather_outbox_v1 WHERE confirmed=0 ORDER BY sequence LIMIT ?', (MAX_ROWS,))]
            result = pack_batch(rows, pending, device_id, max_bytes)
            db.commit()
            return result
        except BaseException:
            db.rollback()
            raise


def acknowledge(path, device_id, request):
    validate_ack(request, device_id)
    string(request['device_id'])
    with closing(connect(path)) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            initialize(db, device_id)
            for row in request['rows']:
                pair = (row['observation_id'], row['revision_hash'])
                found = db.execute('SELECT row_json FROM weather_outbox_v1 WHERE observation_id=? AND revision_hash=?', pair).fetchone()
                if found is None:
                    raise ValueError('weather_ack_unknown_revision')
                validate_row(json.loads(found[0]))
            for row in request['rows']:
                db.execute('UPDATE weather_outbox_v1 SET confirmed=1 WHERE observation_id=? AND revision_hash=?', (row['observation_id'], row['revision_hash']))
            db.commit()
        except BaseException:
            db.rollback()
            raise
    return dict(protocol=PROTOCOL, protocol_version=1, device_id=device_id, confirmed=len(request['rows']))


def command(base, device_id, operation, stdin, stdout):
    """Called only for the two dedicated SSH commands; diagnostics contain no data."""
    path = base / 'data/weather.sqlite3'
    if operation == 'weather_export':
        result = export_batch(path, device_id)
    elif operation == 'weather_ack':
        result = acknowledge(path, device_id, decode(stdin.read(MAX_BYTES + 1)))
    else:
        raise ValueError('weather_unknown_operation')
    raw = canonical(result)
    if len(raw) > MAX_BYTES:
        raise ValueError('weather_response_too_large')
    stdout.write(raw)
