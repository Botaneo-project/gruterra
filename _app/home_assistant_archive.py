"""Transactional HA staging archive; never writes the plant measurements table."""
from contextlib import closing
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3
from home_assistant_client import validate_config
from home_assistant_history import decode_history
from home_assistant_registry import authorized_selection
from home_assistant_sensors import prepare, utc
from sensor_source_policy import hardware_id


def canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def scope(config):
    return digest({'version': 1, 'instance_id': config['instance_id'], 'entities': sorted([
        {key: row[key] for key in ('entity_id', 'device_id', 'model', 'metric')} |
        {'hardware_id': hardware_id(row['hardware_id'])} for row in config['entities']], key=lambda row: row['entity_id'])})


def _check_path(path, plant_db_path=None):
    if plant_db_path is None:
        from database import DB_PATH
        plant_db_path = DB_PATH
    path = Path(path).resolve()
    if path == Path(plant_db_path).resolve():
        raise ValueError('plant_database_forbidden')
    if path.is_file():
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name IN ('plantes','capteurs','mesures') LIMIT 1").fetchone():
                raise ValueError('plant_database_forbidden')
    return path


def checkpoint(path, config, *, plant_db_path=None):
    path = _check_path(path, plant_db_path)
    if not path.is_file():
        return None
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ha_cursor_v1'").fetchone():
            return None
        row = db.execute('SELECT end_time FROM ha_cursor_v1 WHERE scope=?', (scope(config),)).fetchone()
        return row[0] if row else None


def commit_history(path, config, batch, *, plant_db_path=None):
    """Recheck real ownership, validate all rows, then commit rows and cursor.

    Cursor means HA response durably staged, never proof of physical completeness.
    Revisions remain separate and conflicting facts must not enter plant analysis.
    """
    validate_config(config)
    authorized_selection(config['entities'], db_path=plant_db_path)
    if not isinstance(batch, dict) or batch.get('ok') is not True or batch.get('http_status') != 200:
        raise ValueError('unconfirmed_history')
    start, end = utc(batch.get('start')), utc(batch.get('end'))
    mappings = {row['entity_id']: row for row in config['entities']}
    decode_history([], config['entities'], instance_id=config['instance_id'], start=start, end=end,
                   received_at='2000-01-01T00:00:00Z')
    records = batch.get('records')
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError('invalid_history')
    staged = []
    for record in records:
        if not isinstance(record, dict) or record.get('entity_id') not in mappings:
            raise ValueError('invalid_history')
        mapping = mappings[record['entity_id']]
        rebuilt = prepare(record.get('raw_state'), mapping, instance_id=config['instance_id'],
                          received_at=record.get('received_at'), max_age_seconds=7200)
        if rebuilt != record or record['ha_updated_at'] is None or not datetime.fromisoformat(start) <= datetime.fromisoformat(record['ha_updated_at']) < datetime.fromisoformat(end):
            raise ValueError('invalid_history')
        physical = hardware_id(mapping['hardware_id'])
        fact = digest([physical, record['metric'], record['ha_updated_at']])
        value = record['value']
        if value is not None:
            decimal = Decimal(value)
            value = '0' if decimal == 0 else format(decimal.normalize(), 'f')
        semantic = {'value': value, 'unit': 'lx' if record['unit'] == 'lux' else record['unit'],
                    'status': record['status'], 'model': record['model'], 'calibration': record['calibration']}
        revision = digest(semantic)
        staged.append((record, physical, fact, revision, canonical(semantic)))
    if sum(len(canonical(record).encode()) for record in records) > 4*1024*1024:
        raise ValueError('history_too_large')
    path = _check_path(path, plant_db_path)
    stream = scope(config)
    receipt = digest([stream, start, end, sorted(set(row[0]['observation_id'] for row in staged))])
    counts = {'facts_added': 0, 'revisions_added': 0, 'envelopes_added': 0, 'duplicates': 0}
    with closing(sqlite3.connect(path, timeout=5)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute('CREATE TABLE IF NOT EXISTS ha_facts_v1 (fact_id TEXT PRIMARY KEY, physical_id TEXT NOT NULL, metric TEXT NOT NULL, ha_time TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS ha_fact_versions_v1 (fact_id TEXT NOT NULL, revision TEXT NOT NULL, content_json TEXT NOT NULL, PRIMARY KEY(fact_id, revision))')
            db.execute('CREATE TABLE IF NOT EXISTS ha_envelopes_v1 (physical_id TEXT NOT NULL, observation_id TEXT NOT NULL, fact_id TEXT NOT NULL, revision TEXT NOT NULL, record_json TEXT NOT NULL, PRIMARY KEY(physical_id, observation_id))')
            db.execute('CREATE TABLE IF NOT EXISTS ha_cursor_v1 (scope TEXT PRIMARY KEY, end_time TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS ha_windows_v1 (receipt TEXT PRIMARY KEY, scope TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL)')
            cursor = db.execute('SELECT end_time FROM ha_cursor_v1 WHERE scope=?', (stream,)).fetchone()
            if cursor and datetime.fromisoformat(start) > datetime.fromisoformat(cursor[0]):
                raise ValueError('history_gap')
            for record, physical, fact, revision, semantic in staged:
                counts['facts_added'] += db.execute('INSERT OR IGNORE INTO ha_facts_v1 VALUES (?, ?, ?, ?)', (fact, physical, record['metric'], record['ha_updated_at'])).rowcount
                counts['revisions_added'] += db.execute('INSERT OR IGNORE INTO ha_fact_versions_v1 VALUES (?, ?, ?)', (fact, revision, semantic)).rowcount
                added = db.execute('INSERT OR IGNORE INTO ha_envelopes_v1 VALUES (?, ?, ?, ?, ?)', (physical, record['observation_id'], fact, revision, canonical(record))).rowcount
                counts['envelopes_added'] += added
                counts['duplicates'] += 1-added
            db.execute('INSERT OR IGNORE INTO ha_windows_v1 VALUES (?, ?, ?, ?)', (receipt, stream, start, end))
            if not cursor or datetime.fromisoformat(end) > datetime.fromisoformat(cursor[0]):
                db.execute('INSERT OR REPLACE INTO ha_cursor_v1 VALUES (?, ?)', (stream, end))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {'ok': True, 'receipt': receipt, **counts, 'checkpoint': checkpoint(path, config, plant_db_path=plant_db_path),
            'coverage': 'ha_response_staged_only', 'eligible_for_plant_history': False}
