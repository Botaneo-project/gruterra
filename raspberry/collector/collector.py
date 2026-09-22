"""Collecteur Mi Flora autonome. Aucun effacement du capteur, aucun envoi PC."""
import argparse
import asyncio
import fcntl
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / 'botaneo'


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=20)
    try:
        db.execute('PRAGMA synchronous=FULL')
        with db:
            yield db
    finally:
        db.close()


def initialize(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS measurements (
            measurement_id TEXT PRIMARY KEY, device_id TEXT NOT NULL,
            sensor_id TEXT NOT NULL, measured_at TEXT NOT NULL,
            time_quality TEXT NOT NULL, boot_id TEXT NOT NULL, uptime_seconds REAL NOT NULL,
            temperature_c REAL NOT NULL, moisture_percent INTEGER NOT NULL,
            illuminance_lux INTEGER NOT NULL, conductivity_us_cm INTEGER NOT NULL,
            raw TEXT NOT NULL, schema_version INTEGER NOT NULL DEFAULT 1,
            sync_state TEXT NOT NULL DEFAULT 'pending' CHECK(sync_state IN ('pending','confirmed')),
            confirmed_at TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS sensor_status (
            sensor_id TEXT PRIMARY KEY, last_attempt TEXT NOT NULL,
            last_success TEXT, last_error TEXT, consecutive_failures INTEGER NOT NULL DEFAULT 0)''')
        db.execute('CREATE INDEX IF NOT EXISTS pending_measurements ON measurements(sync_state, measured_at)')


def clock_synced():
    try:
        return subprocess.run(['timedatectl', 'show', '-p', 'NTPSynchronized', '--value'],
                              capture_output=True, text=True, timeout=5).stdout.strip() == 'yes'
    except (OSError, subprocess.TimeoutExpired):
        return False


def record(path, device_id, sensor_id, values=None, error=None):
    at = datetime.now(timezone.utc).isoformat()
    with connect(path) as db:
        if values is not None:
            temp, moisture, light, conductivity, raw = values
            if not -20 <= temp <= 60 or not 0 <= moisture <= 100 or light < 0 or conductivity < 0:
                raise ValueError('Invalid sensor measurement')
            identifier = str(uuid.uuid4())
            db.execute('''INSERT INTO measurements (
                measurement_id,device_id,sensor_id,measured_at,time_quality,boot_id,uptime_seconds,
                temperature_c,moisture_percent,illuminance_lux,conductivity_us_cm,raw)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
                identifier, device_id, sensor_id, at, 'ntp' if clock_synced() else 'unverified',
                Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                float(Path('/proc/uptime').read_text().split()[0]), temp, moisture, light, conductivity, raw))
            db.execute('''INSERT INTO sensor_status VALUES (?,?,?,NULL,0)
                ON CONFLICT(sensor_id) DO UPDATE SET last_attempt=excluded.last_attempt,
                last_success=excluded.last_success,last_error=NULL,consecutive_failures=0''', (sensor_id, at, at))
            return identifier
        db.execute('''INSERT INTO sensor_status VALUES (?,?,NULL,?,1)
            ON CONFLICT(sensor_id) DO UPDATE SET last_attempt=excluded.last_attempt,
            last_error=excluded.last_error,consecutive_failures=consecutive_failures+1''', (sensor_id, at, error))


async def cycle(config, path, reader, history_reader=None):
    for sensor in config['sensors']:
        if history_reader:
            try:
                status, count = await asyncio.wait_for(history_reader(path, config['device_id'], sensor), timeout=600)
                logging.info('Historique %s : %s entrees lues (deduplication active)', status, count)
            except Exception as exc:
                logging.warning('Historique indisponible ou partiel (%s); mesure directe maintenue', type(exc).__name__)
        try:
            values = await asyncio.wait_for(reader(sensor, silencieux=True), timeout=100)
        except Exception as exc:
            # Type uniquement : pas d’identifiant privé dans les journaux.
            record(path, config['device_id'], sensor, error=type(exc).__name__)
            logging.warning('Lecture capteur indisponible (%s)', type(exc).__name__)
        else:
            # Une erreur de stockage doit arrêter le processus pour permettre une reprise visible.
            record(path, config['device_id'], sensor, values=values)
            logging.info('Mesure enregistree, en attente de synchronisation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    config = json.loads((BASE / 'config/collector.json').read_text())
    interval = config['interval_seconds']
    if type(interval) is not int or interval < 60:
        raise ValueError('Interval must be >= 60 seconds')
    if not config.get('device_id') or not config.get('sensors'):
        raise ValueError('Collector identity and sensors required')
    import re
    if not all(isinstance(s, str) and re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', s) for s in config['sensors']):
        raise ValueError('Invalid sensor address')
    data = BASE / 'data'
    data.mkdir(exist_ok=True)
    lock = (data / 'collector.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Collector already running')
    path = data / 'collector.sqlite3'
    initialize(path)
    sys.path.insert(0, str(BASE / 'releases/20260916/_app'))
    from capteurs.miflora import lire_mesure
    from history_store import collect as history_reader
    logging.info('Collecteur actif; intervalle %s secondes', interval)
    request = data / 'collect.request'
    state = data / 'collect-state.json'
    def publish(value):
        temporary = state.with_suffix('.tmp')
        temporary.write_text(json.dumps(value))
        os.replace(temporary, state)
    while True:
        publish({'running': True, 'message': 'Lecture des capteurs en cours…'})
        request.unlink(missing_ok=True)
        asyncio.run(cycle(config, path, lire_mesure, history_reader))
        with connect(path) as db:
            failures = db.execute('SELECT COUNT(*) FROM sensor_status WHERE last_error IS NOT NULL').fetchone()[0]
        publish({'running': False, 'message': 'Collecte terminée.' if not failures else 'Collecte terminée avec une erreur : voir le capteur.',
                 'finished_at': datetime.now(timezone.utc).isoformat()})
        if args.once:
            return
        # Pas de dépendance au Wi-Fi. Après redémarrage, nouvelle lecture immédiate.
        deadline = time.monotonic() + interval
        while time.monotonic() < deadline and not request.exists():
            time.sleep(1)


if __name__ == '__main__':
    main()
