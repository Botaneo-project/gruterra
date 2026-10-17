"""Copy weather snapshots over existing SSH; never replace a live database."""
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from contextlib import closing

def verify(path,meta):
    data=Path(path).read_bytes()
    if len(data)!=meta['size'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:
        raise ValueError('weather_backup_checksum')
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('weather_backup_integrity')
        for table in ('weather_identity','weather_outbox_v1'):db.execute('SELECT count(*) FROM '+table).fetchone()

def retrieve(config,folder=None):
    from suivi_raspberry import validate
    validate(config)
    folder=Path(folder or Path(__file__).resolve().parents[1]/'_security_backups/raspberry_weather')/hashlib.sha256(config['device_id'].encode()).hexdigest()[:16]
    folder.mkdir(parents=True,exist_ok=True)
    host=config['user']+'@'+config['host']
    opts=['-i',config['key'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8']
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    meta=json.loads(subprocess.run(['ssh',*opts,host,'python3 ~/botaneo/collector/weather_backup.py manifest'],capture_output=True,text=True,timeout=30,check=True,creationflags=flags).stdout)
    if not isinstance(meta,dict) or set(meta)!= {'name','size','sha256'}:raise ValueError('weather_backup_metadata')
    if not isinstance(meta['name'],str) or not re.fullmatch(r'weather-[0-9]{4}-[0-9]{2}-[0-9]{2}\.sqlite3',meta['name']):raise ValueError('weather_backup_metadata')
    if type(meta['size']) is not int or not 0<meta['size']<=100*1024*1024:raise ValueError('weather_backup_metadata')
    if not isinstance(meta['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',meta['sha256']):raise ValueError('weather_backup_metadata')
    target=folder/meta['name']
    if target.exists():
        try:verify(target,meta);return 'verified'
        except (ValueError,sqlite3.Error):pass
    fd,tmp=tempfile.mkstemp(dir=folder,suffix='.part');os.close(fd)
    try:
        subprocess.run(['scp',*opts,host+':botaneo/backups/weather/'+meta['name'],tmp],capture_output=True,timeout=120,check=True,creationflags=flags)
        verify(tmp,meta)
        with open(tmp,'r+b') as stream:os.fsync(stream.fileno())
        os.replace(tmp,target)
        return 'copied'
    finally:Path(tmp).unlink(missing_ok=True)
