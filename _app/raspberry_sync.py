"""Pi first: durable receipts, replay-safe import, acknowledgement after commit."""
import hashlib
import json
import math
import sqlite3
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

LOCK = threading.Lock()


def digest(item):
    return hashlib.sha256(json.dumps(item, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def config_path():
    from botaneo_config import CONFIG_DIR
    return Path(CONFIG_DIR) / 'raspberry.local.json'


def owned(address):
    # Keep ownership independent of availability/away: no surprise BLE fallback.
    config = json.loads(config_path().read_text(encoding='utf-8-sig'))
    return str(address).upper() in [s.upper() for s in config.get('sensors', [])]


def transport(config, operation, request=None):
    from suivi_raspberry import validate
    validate(config)
    args = ['ssh', '-i', config['key'], '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8',
            '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2',
            config['user']+'@'+config['host'],
            'python3 ~/botaneo/collector/sync_export.py '+operation]
    result = subprocess.run(args, input=json.dumps(request) if request is not None else None,
                            capture_output=True, text=True, timeout=60,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise ConnectionError('Raspberry inaccessible ou transfert refusé. Données conservées, nouvel essai possible.')
    return json.loads(result.stdout)


def import_batch(db_path, batch, config):
    if batch.get('version') != 1 or batch.get('device_id') != config['device_id'] or len(batch['rows']) > 500:
        raise ValueError('Identité ou format du collecteur incorrect.')
    counts = {'added': 0, 'duplicates': 0, 'undated': 0}
    ack = []
    db = sqlite3.connect(Path(db_path).resolve().as_uri()+'?mode=rw', uri=True, timeout=30)
    try:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        db.execute('''CREATE TABLE IF NOT EXISTS raspberry_receipts (
            device_id TEXT NOT NULL, measurement_id TEXT NOT NULL, digest TEXT NOT NULL,
            payload TEXT NOT NULL, received_at TEXT NOT NULL, disposition TEXT NOT NULL,
            PRIMARY KEY(device_id,measurement_id))''')
        db.execute('''CREATE TABLE IF NOT EXISTS historique_miflora_brut (
            id INTEGER PRIMARY KEY AUTOINCREMENT, capteur_id INTEGER NOT NULL,
            index_capteur INTEGER NOT NULL, timestamp_capteur INTEGER, date_heure_utc TEXT,
            temperature REAL, humidite REAL, luminosite REAL, conductivite REAL,
            raw_hex TEXT NOT NULL, import_date TEXT NOT NULL, statut TEXT NOT NULL DEFAULT 'importe',
            UNIQUE(capteur_id,raw_hex))''')
        for row in batch['rows']:
            checksum = digest(row)
            if row['device_id'] != config['device_id'] or row['schema_version'] != 1 or row['kind'] not in ('history', 'current'):
                raise ValueError('Mesure incompatible.')
            previous = db.execute('SELECT digest FROM raspberry_receipts WHERE device_id=? AND measurement_id=?',
                                  (row['device_id'], row['measurement_id'])).fetchone()
            if previous:
                if previous[0] != checksum:
                    raise ValueError('Identifiant réutilisé avec un contenu différent.')
                counts['duplicates'] += 1
            else:
                sensors = db.execute('SELECT id,plante_id,actif FROM capteurs WHERE UPPER(adresse_ble)=?',
                                     (row['sensor_id'].upper(),)).fetchall()
                if row['sensor_id'].upper() not in [s.upper() for s in config['sensors']] or len(sensors) != 1 or sensors[0][1] is None or not sensors[0][2]:
                    raise ValueError('Affectation du capteur absente, inactive ou ambiguë ; transfert non confirmé.')
                values = [row[k] for k in ('temperature_c', 'moisture_percent', 'illuminance_lux', 'conductivity_us_cm')]
                if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values) or not -20 <= values[0] <= 60 or not 0 <= values[1] <= 100 or min(values[2:]) < 0:
                    raise ValueError('Valeurs invalides.')
                raw = bytes.fromhex(row['raw']).hex()
                if row['kind'] == 'history':
                    frame = bytes.fromhex(raw)
                    if len(frame) != 16 or int.from_bytes(frame[:4], 'little') != row['sensor_seconds']:
                        raise ValueError('Historique brut invalide.')
                    decoded = [int.from_bytes(frame[4:6], 'little', signed=True)/10, frame[11],
                               int.from_bytes(frame[7:11], 'little'), int.from_bytes(frame[12:14], 'little')]
                    if decoded != values:
                        raise ValueError('Historique incohérent.')
                    # Legacy archive deduplicates by raw frame; do not rewrite its dates.
                    # -1 explicitly means that the collector did not retain the ring-buffer index.
                    db.execute('''INSERT OR IGNORE INTO historique_miflora_brut
                        (capteur_id,index_capteur,timestamp_capteur,date_heure_utc,temperature,
                         humidite,luminosite,conductivite,raw_hex,import_date,statut)
                        VALUES (?,-1,?,?,?,?,?,?,?,?,?)''',
                        (sensors[0][0], row['sensor_seconds'],
                         row['measured_at'] if row['time_quality'] == 'estimated_from_sensor_clock' else None,
                         *values, raw, datetime.now(timezone.utc).isoformat(), 'raspberry_'+row['time_quality']))
                disposition = 'undated'
                quality = 'estimated_from_sensor_clock' if row['kind'] == 'history' else 'ntp'
                if row['measured_at'] and row['time_quality'] == quality:
                    instant = datetime.fromisoformat(row['measured_at'])
                    if instant.tzinfo is None or instant > datetime.now(timezone.utc):
                        raise ValueError('Date invalide.')
                    date = instant.astimezone().replace(tzinfo=None).isoformat(timespec='seconds')
                    # History contains internal time: absorb clock estimation drift.
                    tolerance = 120 if row['kind'] == 'history' else 1
                    duplicate = db.execute('''SELECT 1 FROM mesures WHERE capteur_id=?
                        AND LOWER(REPLACE(donnees_brutes,' ',''))=?
                        AND ABS(julianday(date_heure)-julianday(?))*86400 < ? LIMIT 1''',
                        (sensors[0][0], raw, date, tolerance)).fetchone()
                    disposition = 'duplicates' if duplicate else 'added'
                    if not duplicate:
                        db.execute('''INSERT INTO mesures(date_heure,temperature,humidite,luminosite,
                            conductivite,donnees_brutes,capteur_id) VALUES (?,?,?,?,?,?,?)''',
                            (date, *values, raw, sensors[0][0]))
                counts[disposition] += 1
                db.execute('INSERT INTO raspberry_receipts VALUES (?,?,?,?,?,?)',
                           (row['device_id'], row['measurement_id'], checksum, json.dumps(row),
                            datetime.now(timezone.utc).isoformat(), disposition))
            ack.append({'kind': row['kind'], 'measurement_id': row['measurement_id'], 'digest': checksum})
        db.commit()
        return counts, {'device_id': config['device_id'], 'rows': ack}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def synchronize(config=None, sender=transport, db_path=None):
    import database
    from suivi_raspberry import load_config
    config = config or load_config(config_path())
    if config.get('away') or not config.get('enabled'):
        return {'ok': False, 'message': 'Synchronisation Raspberry suspendue dans les réglages.'}
    with LOCK:
        totals = {'added': 0, 'duplicates': 0, 'undated': 0}
        try:
            # Bounded work: remaining batches resume at the next retry.
            for _ in range(20):
                batch = sender(config, 'export')
                counts, ack = import_batch(db_path or database.DB_PATH, batch, config)
                for key in totals:
                    totals[key] += counts[key]
                if ack['rows']:
                    response = sender(config, 'ack', ack)
                    if response.get('confirmed') != len(ack['rows']):
                        raise ValueError('Confirmation du Raspberry incomplète.')
                if batch['pending'] <= len(batch['rows']):
                    backup_message = ''
                    if sender is transport and db_path is None:
                        try:
                            from raspberry_backup import retrieve
                            backup_message = retrieve(config, Path(database.DB_PATH).parent.parent / '_security_backups/raspberry_daily')
                        except Exception:
                            backup_message = 'Mesures reçues ; sauvegarde Pi non copiée, nouvel essai à la prochaine synchronisation.'
                    return {'backup_message': backup_message, 'ok': True, 'message': backup_message + ' ' + f"Raspberry : {totals['added']} mesure(s) ajoutée(s), {totals['duplicates']} déjà reçue(s), {totals['undated']} sans date fiable conservée(s).", **totals}
            raise RuntimeError('Transfert partiel conservé ; suite au prochain essai.')
        except Exception as error:
            message = str(error) if isinstance(error, (ValueError, ConnectionError, RuntimeError)) else 'Transfert interrompu ; reprise sans doublons au prochain essai.'
            return {'ok': False, 'message': message, **totals}
