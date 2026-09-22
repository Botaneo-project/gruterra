import json
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path.home() / 'botaneo/data/collector.sqlite3')
db.row_factory = sqlite3.Row
result = {'integrity': db.execute('PRAGMA integrity_check').fetchone()[0],
          'count': db.execute('SELECT COUNT(*) FROM measurements').fetchone()[0],
          'latest': [dict(row) for row in db.execute('SELECT measured_at,temperature_c,moisture_percent,illuminance_lux,conductivity_us_cm,time_quality,sync_state FROM measurements ORDER BY rowid DESC LIMIT 2')],
          'sensors': [dict(row) for row in db.execute('SELECT * FROM sensor_status')]}
print(json.dumps(result))
db.close()
