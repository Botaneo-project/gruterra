"""Expose only metadata for the latest daily SQLite snapshot over SSH."""
import hashlib,json
from pathlib import Path
folder=Path.home()/'botaneo/backups/daily'
files=sorted(folder.glob('collector-????-??-??.sqlite3'))
if not files:
    raise SystemExit('No daily backup available')
p=files[-1]
data=p.read_bytes()
print(json.dumps({'name':p.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}))
