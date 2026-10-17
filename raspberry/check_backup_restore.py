"""Rehearse recovery into temporary copies; never replace live databases."""
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path


def counts(path, tables):
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Invalid backup')
        return {name: db.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0] for name in tables}


def main():
    os.umask(0o077)
    base = Path.home() / 'botaneo'
    sys.path.insert(0, str(base / 'collector'))
    import web_status
    results = {}
    with tempfile.TemporaryDirectory(prefix='gruterra-restore-') as temporary:
        for kind, pattern, tables in (
            ('daily', 'collector-????-??-??.sqlite3', ('measurements', 'history_measurements', 'sensor_status')),
            ('weather', 'weather-????-??-??.sqlite3', ('weather_identity', 'weather_outbox_v1')),
        ):
            candidates = sorted((base / 'backups' / kind).glob(pattern))
            if not candidates:
                raise ValueError('Backup unavailable')
            source = candidates[-1]
            digest = hashlib.sha256(source.read_bytes()).digest()
            expected = counts(source, tables)
            restored = Path(temporary) / source.name
            shutil.copyfile(source, restored)
            if hashlib.sha256(restored.read_bytes()).digest() != digest:
                raise ValueError('Copy mismatch')
            if counts(restored, tables) != expected:
                raise ValueError('Restored rows mismatch')
            # Verify that the current application can actually read the recovered schema.
            if kind == 'daily':
                view = web_status.snapshot(restored)
                if view['history'] != expected['history_measurements']:
                    raise ValueError('Application read mismatch')
            else:
                view = web_status.weather_snapshot(restored)
                if view['total'] != expected['weather_outbox_v1']:
                    raise ValueError('Application read mismatch')
            # A recovered copy must also support future writes, tested by rollback.
            with closing(sqlite3.connect(restored)) as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('CREATE TABLE restore_probe (value INTEGER)')
                db.execute('INSERT INTO restore_probe VALUES (1)')
                db.rollback()
                if db.execute("SELECT count(*) FROM sqlite_master WHERE name='restore_probe'").fetchone()[0]:
                    raise ValueError('Rollback failed')
            if hashlib.sha256(source.read_bytes()).digest() != digest:
                raise ValueError('Source changed during check')
            results[kind] = {'backup': source.name, 'counts': expected, 'application_read': True, 'write_rollback': True}
    print(json.dumps({'status': 'verified_on_temporary_copies', 'results': results}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('backup_restore_check_failed', file=sys.stderr)
        raise SystemExit(1)
