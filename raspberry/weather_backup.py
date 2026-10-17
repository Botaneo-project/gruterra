"""Consistent weather snapshots; no credentials or automatic data restoration."""
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

TABLES = ('weather_identity', 'weather_outbox_v1')

def verify(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('weather_backup_invalid')
        for table in TABLES:
            db.execute('SELECT count(*) FROM '+table).fetchone()

def backup(base):
    base=Path(base)
    source=base/'data/weather.sqlite3'
    if not source.exists():return {'status':'not_initialized'}
    folder=base/'backups/weather'
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    name='weather-'+datetime.now(timezone.utc).strftime('%Y-%m-%d')+'.sqlite3'
    fd,tmp=tempfile.mkstemp(prefix='.weather-',suffix='.part',dir=folder)
    os.close(fd)
    temporary=Path(tmp)
    try:
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as src:
            with closing(sqlite3.connect(temporary)) as dst:src.backup(dst)
        verify(temporary)
        os.chmod(temporary,0o600)
        with temporary.open('r+b') as stream:os.fsync(stream.fileno())
        os.replace(temporary,folder/name)
        for old in sorted(folder.glob('weather-????-??-??.sqlite3'),reverse=True)[14:]:old.unlink()
        return {'status':'verified','name':name}
    finally:temporary.unlink(missing_ok=True)

def manifest(base):
    files=sorted((Path(base)/'backups/weather').glob('weather-????-??-??.sqlite3'))
    if not files:raise ValueError('weather_backup_unavailable')
    path=files[-1]
    verify(path)
    data=path.read_bytes()
    return {'name':path.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}

if __name__=='__main__':
    import sys
    os.umask(0o077)
    try:
        if sys.argv[1:]==['manifest']:result=manifest(Path.home()/'botaneo')
        elif not sys.argv[1:]:result=backup(Path.home()/'botaneo')
        else:raise ValueError('weather_backup_operation')
        print(json.dumps(result))
    except Exception:
        print('weather_backup_failed',file=sys.stderr)
        raise SystemExit(1)
