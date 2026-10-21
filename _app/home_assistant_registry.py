"""Read-only bridge from existing BLE registrations to HA import policy."""
from collections import Counter
from contextlib import closing
from pathlib import Path
import sqlite3
from sensor_source_policy import hardware_id, authorize_ha_mappings
from home_assistant_sensors import validate_device_profile


def read_ble_inventory(db_path=None):
    if db_path is None:
        from database import DB_PATH
        db_path = DB_PATH
    path = Path(db_path).resolve()
    if not path.is_file():
        raise ValueError('registry_unavailable')
    try:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
            rows = db.execute('SELECT adresse_ble FROM capteurs').fetchall()
        return [hardware_id('ble:'+row[0]).split(':', 1)[1] for row in rows]
    except Exception:
        raise ValueError('registry_unavailable') from None


def assess_mappings(mappings, *, db_path=None):
    try:
        registered = {'ble:'+value for value in read_ble_inventory(db_path)}
    except ValueError:
        return ['registry_unavailable'] * len(mappings)
    physical = []
    for row in mappings:
        try:
            physical.append(hardware_id(row.get('hardware_id')))
        except ValueError:
            physical.append(None)
    counts = Counter((key, row.get('metric')) for key, row in zip(physical, mappings) if key)
    statuses = []
    for key, row in zip(physical, mappings):
        if not key:
            status = 'identity_pending'
        elif key in registered:
            status = 'already_ble'
        elif counts[(key, row.get('metric'))] > 1:
            status = 'duplicate'
        elif row.get('hardware_confirmed') is not True:
            status = 'identity_pending'
        else:
            try:
                validate_device_profile(row)
            except ValueError:
                status = 'identity_pending'
            else:
                status = 'authorized'
        statuses.append(status)
    return statuses


def authorized_selection(mappings, *, db_path=None):
    """Read current DB on each attempt; never trust a status saved earlier."""
    states = assess_mappings(mappings, db_path=db_path)
    if not mappings or any(state != 'authorized' for state in states):
        raise ValueError('mapping_not_authorized')
    ble = read_ble_inventory(db_path)
    owners = {hardware_id(row['hardware_id']): 'home_assistant' for row in mappings}
    authorize_ha_mappings(mappings, owners, existing_ble_addresses=ble)
    return owners, ble


def preview(config, mappings, *, received_at, db_path=None, requester=None):
    """Manual, read-only snapshot; no archive/import, scheduler or activation."""
    if __import__('os').environ.get('BOTANEO_DEMO') == '1':
        return {'ok': False, 'code': 'demo_disabled', 'http_status': None, 'records': []}
    from home_assistant_client import read_snapshot
    try:
        authorized_selection(mappings, db_path=db_path)
    except ValueError:
        return {'ok': False, 'code': 'mapping_not_authorized', 'http_status': None, 'records': []}
    return read_snapshot({**config, 'enabled': True, 'entities': mappings}, received_at=received_at, requester=requester)
