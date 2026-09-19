"""Consistent SQLite backup, verified before rotation (14 daily snapshots)."""
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

base = Path.home() / 'botaneo'
folder = base / 'backups/daily'
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
target = folder / ('collector-' + datetime.now(timezone.utc).strftime('%Y-%m-%d') + '.sqlite3')
temporary = folder / 'backup-in-progress.sqlite3'
with closing(sqlite3.connect((base/'data/collector.sqlite3').as_uri()+'?mode=ro', uri=True)) as source:
    with closing(sqlite3.connect(temporary)) as destination:
        source.backup(destination, pages=128, sleep=0.1)
        if destination.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Backup integrity failed')
        counts = {table: destination.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                  for table in ('measurements', 'history_measurements')}
os.chmod(temporary, 0o600)
with temporary.open('rb') as stream:
    os.fsync(stream.fileno())
os.replace(temporary, target)
for old in sorted(folder.glob('collector-????-??-??.sqlite3'), reverse=True)[14:]:
    old.unlink()
print('Verified backup:', target.name, counts, flush=True)
