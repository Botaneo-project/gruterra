"""Historique brut durable, distinct des lectures instantanées."""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from collector import connect, clock_synced
from history_protocol import lire_historique


def initialize(path):
    with connect(path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS history_epochs (
            sensor_id TEXT PRIMARY KEY, epoch TEXT NOT NULL, last_seconds INTEGER NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS history_runs (
            run_id TEXT PRIMARY KEY, sensor_id TEXT NOT NULL, started_at TEXT NOT NULL,
            finished_at TEXT, status TEXT NOT NULL, expected INTEGER, received INTEGER NOT NULL DEFAULT 0,
            clock_json TEXT, error TEXT)''')
        db.execute('''CREATE TABLE IF NOT EXISTS history_measurements (
            measurement_id TEXT PRIMARY KEY, device_id TEXT NOT NULL, sensor_id TEXT NOT NULL,
            epoch TEXT NOT NULL, sensor_seconds INTEGER NOT NULL, raw TEXT NOT NULL,
            measured_at TEXT, time_quality TEXT NOT NULL, received_at TEXT NOT NULL,
            temperature_c REAL NOT NULL, moisture_percent INTEGER NOT NULL,
            illuminance_lux INTEGER NOT NULL, conductivity_us_cm INTEGER NOT NULL,
            schema_version INTEGER NOT NULL DEFAULT 1, sync_state TEXT NOT NULL DEFAULT 'pending',
            UNIQUE(sensor_id,epoch,raw))''')


class Import:
    def __init__(self, path, device, sensor):
        self.path, self.device, self.sensor = path, device, sensor
        self.run = str(uuid.uuid4())
        self.epoch = None
        self.received = 0
        self.synced = clock_synced()
        initialize(path)
        with connect(path) as db:
            db.execute("UPDATE history_runs SET status='interrupted' WHERE sensor_id=? AND status='running'", (sensor,))
            db.execute("INSERT INTO history_runs(run_id,sensor_id,started_at,status) VALUES (?,?,?,'running')",
                       (self.run, sensor, datetime.now(timezone.utc).isoformat()))

    def start(self, export):
        seconds = export['clock_before']['device_seconds']
        if seconds is None:
            raise ValueError('Sensor clock unavailable')
        with connect(self.path) as db:
            old = db.execute('SELECT epoch,last_seconds FROM history_epochs WHERE sensor_id=?', (self.sensor,)).fetchone()
            epoch = old[0] if old and seconds >= old[1] else str(uuid.uuid4())
            if self.epoch is not None and epoch != self.epoch:
                raise ValueError('Sensor clock reset during import')
            self.epoch = epoch
            db.execute('INSERT OR REPLACE INTO history_epochs VALUES (?,?,?)', (self.sensor, self.epoch, seconds))
            db.execute('UPDATE history_runs SET expected=?,clock_json=? WHERE run_id=?',
                       (export['history_count'], json.dumps(export['clock_before']), self.run))

    def entry(self, entry):
        at = entry.get('date_heure_utc') if self.synced else None
        with connect(self.path) as db:
            db.execute('''INSERT INTO history_measurements (
                measurement_id,device_id,sensor_id,epoch,sensor_seconds,raw,measured_at,time_quality,
                received_at,temperature_c,moisture_percent,illuminance_lux,conductivity_us_cm)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(sensor_id,epoch,raw) DO NOTHING''',
                (str(uuid.uuid4()), self.device, self.sensor, self.epoch, entry['timestamp_capteur'],
                 entry['raw_hex'], at, 'estimated_from_sensor_clock' if at else 'unverified',
                 datetime.now(timezone.utc).isoformat(), entry['temperature'], entry['humidite'],
                 entry['luminosite'], entry['conductivite']))
            self.received += 1
            db.execute('UPDATE history_runs SET received=? WHERE run_id=?', (self.received, self.run))

    def finish(self, status, error=None):
        with connect(self.path) as db:
            db.execute('UPDATE history_runs SET status=?,error=?,finished_at=? WHERE run_id=?',
                       (status, error, datetime.now(timezone.utc).isoformat(), self.run))
            db.execute('DELETE FROM history_runs WHERE rowid NOT IN (SELECT rowid FROM history_runs ORDER BY rowid DESC LIMIT 100)')


async def collect(path, device_id, sensor):
    from bleak import BleakScanner, BleakClient
    archive = Import(path, device_id, sensor)
    try:
        device = await BleakScanner.find_device_by_address(sensor, timeout=20)
        if device is None:
            raise TimeoutError('Sensor not found')
        index = 0
        failures = 0
        while True:
            async with BleakClient(device, timeout=25) as client:
                export = await lire_historique(client, sensor, archive.start, archive.entry,
                                               start_index=index, max_entries=20)
            next_index = export['next_index']
            if export['status'] == 'complete':
                break
            failures = failures + 1 if next_index == index else 0
            if failures >= 2:
                break
            index = next_index
            await asyncio.sleep(2)
        errors = export.get('errors', [])
        archive.finish(export['status'], errors[0]['type'] if errors else None)
        return export['status'], archive.received
    except asyncio.CancelledError:
        archive.finish('partial' if archive.received else 'failed', 'TimeoutOrInterrupted')
        raise
    except Exception as error:
        archive.finish('partial' if archive.received else 'failed', type(error).__name__)
        raise
