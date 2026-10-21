"""Confirmed test-only purge in the separate HA archive, with backup and replay guard."""
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
import uuid
from home_assistant_archive import _check_path, digest
from home_assistant_sensors import utc
from sensor_source_policy import hardware_id


def _plan(db, physical, start, end):
    selected = []
    for fact, stamp in db.execute('SELECT fact_id, ha_time FROM ha_facts_v1 WHERE physical_id=? ORDER BY fact_id', (physical,)):
        if not datetime.fromisoformat(start) <= datetime.fromisoformat(stamp) < datetime.fromisoformat(end):
            continue
        rows = db.execute('SELECT record_json FROM ha_envelopes_v1 WHERE fact_id=? ORDER BY observation_id', (fact,)).fetchall()
        # Mixed production/test facts are never eligible for test deletion.
        if rows and all(json.loads(row[0]).get('test_data') is True for row in rows):
            selected.append((fact, [row[0] for row in rows]))
    plan = dict(physical_id=physical, start=start, end=end,
                facts=len(selected), envelopes=sum(len(rows) for _, rows in selected),
                fact_ids=[fact for fact, _ in selected])
    plan['plan_id'] = digest([plan, selected])
    return plan


def preview_test_purge(path, physical, *, start, end, plant_db_path=None):
    path = _check_path(path, plant_db_path)
    physical, start, end = hardware_id(physical), utc(start), utc(end)
    if not datetime.fromisoformat(start) < datetime.fromisoformat(end):
        raise ValueError('invalid_purge_range')
    if not path.is_file():
        raise ValueError('archive_missing')
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
        return _plan(db, physical, start, end)


def purge_test_data(path, plan, *, confirmed=False, plant_db_path=None):
    if confirmed is not True:
        raise ValueError('confirmation_required')
    if os.environ.get('BOTANEO_DEMO') == '1':
        raise ValueError('demo_disabled')
    path = _check_path(path, plant_db_path)
    if not path.is_file():
        raise ValueError('archive_missing')
    physical, start, end = hardware_id(plan['physical_id']), utc(plan['start']), utc(plan['end'])
    with closing(sqlite3.connect(path, timeout=5)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        try:
            fresh = _plan(db, physical, start, end)
            if fresh != plan:
                raise ValueError('plan_changed')
            if not fresh['facts']:
                raise ValueError('no_test_data')
            backup = path.with_name(path.name+'.before-test-purge-'+uuid.uuid4().hex+'.sqlite3')
            # A separate reader sees the same committed state; IMMEDIATE prevents writers.
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(backup)) as target:
                source.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('backup_failed')
            db.execute('CREATE TABLE IF NOT EXISTS ha_excluded_facts_v1 (fact_id TEXT PRIMARY KEY)')
            for fact in fresh['fact_ids']:
                db.execute('INSERT OR IGNORE INTO ha_excluded_facts_v1 VALUES (?)', (fact,))
                db.execute('DELETE FROM ha_envelopes_v1 WHERE fact_id=?', (fact,))
                db.execute('DELETE FROM ha_fact_versions_v1 WHERE fact_id=?', (fact,))
                db.execute('DELETE FROM ha_facts_v1 WHERE fact_id=?', (fact,))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return dict(ok=True, facts_deleted=fresh['facts'], backup=str(backup), replay_blocked=True)
