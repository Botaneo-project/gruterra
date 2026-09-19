"""Fetch verified daily snapshots; never replace the live PC database."""
import hashlib,json,os,re,sqlite3,subprocess,tempfile
from pathlib import Path

def verify(path, metadata):
    if path.stat().st_size != metadata['size'] or hashlib.sha256(path.read_bytes()).hexdigest()!=metadata['sha256']:
        raise ValueError('Incomplete or changed backup')
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    try:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('Invalid SQLite backup')
        for table in ('measurements','history_measurements'):
            db.execute('SELECT COUNT(*) FROM '+table).fetchone()
    finally:
        db.close()

def retrieve(config, folder):
    from suivi_raspberry import validate
    validate(config)
    folder=Path(folder)/hashlib.sha256(config['device_id'].encode()).hexdigest()[:16]
    folder.mkdir(parents=True,exist_ok=True)
    options=['-i',config['key'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes',
             '-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8']
    host=config['user']+'@'+config['host']
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    result=subprocess.run(['ssh',*options,host,'python3 ~/botaneo/collector/backup_manifest.py'],
                          capture_output=True,text=True,timeout=30,creationflags=flags,check=True)
    metadata=json.loads(result.stdout)
    if not re.fullmatch(r'collector-\d{4}-\d{2}-\d{2}\.sqlite3',metadata['name']) or not 0 < metadata['size'] <= 100*1024*1024 or not re.fullmatch('[0-9a-f]{64}',metadata['sha256']):
        raise ValueError('Invalid backup metadata')
    target=folder/metadata['name']
    if target.exists():
        try:
            verify(target,metadata)
            return 'Sauvegarde Pi déjà vérifiée sur le PC ('+metadata['name'][10:20]+').'
        except (ValueError,sqlite3.Error):
            pass
    fd,tmp=tempfile.mkstemp(dir=folder,suffix='.part')
    os.close(fd)
    temporary=Path(tmp)
    try:
        subprocess.run(['scp',*options,host+':botaneo/backups/daily/'+metadata['name'],str(temporary)],
                       capture_output=True,timeout=120,creationflags=flags,check=True)
        verify(temporary,metadata)
        with temporary.open('r+b') as stream: os.fsync(stream.fileno())
        os.replace(temporary,target)
        return 'Sauvegarde Pi copiée et vérifiée sur le PC ('+metadata['name'][10:20]+').'
    finally:
        temporary.unlink(missing_ok=True)

