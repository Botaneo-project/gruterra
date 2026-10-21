"""Offline preparation for explicitly mapped Home Assistant sensor states.

No networking, credentials, database migration or hardware control here.
HA state timestamps are never presented as physical measurement timestamps.
"""
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

UNITS = {'soil_moisture': '%', 'air_humidity': '%', 'temperature': '°C', 'illuminance': 'lx'}

# Capabilities describe supported quantities, never an accuracy guarantee.
ZIGBEE_PROFILES = {
    'ZS-304Z': frozenset(UNITS),
    'ZG-106Z': frozenset(('illuminance',)),
}


def validate_device_profile(mapping):
    model = mapping.get('model', '').strip()
    if model in ZIGBEE_PROFILES:
        if mapping.get('metric') not in ZIGBEE_PROFILES[model]:
            raise ValueError('unsupported_device_metric')
        if mapping.get('hardware_id'):
            from sensor_source_policy import hardware_id
            if not hardware_id(mapping['hardware_id']).startswith('zigbee:'):
                raise ValueError('device_transport_mismatch')
    if 'test_data' in mapping and type(mapping['test_data']) is not bool:
        raise ValueError('invalid_test_marker')



def utc(value):
    if not isinstance(value, str):
        raise ValueError('invalid_timestamp')
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('invalid_timestamp') from None
    if date.tzinfo is None or date.utcoffset() is None:
        raise ValueError('timezone_required')
    return date.astimezone(timezone.utc).isoformat()


def prepare(state, mapping, *, instance_id, received_at, max_age_seconds=7200):
    """Mapping approved manually; model and calibration are never inferred.

    State content is retained locally as HA data, not a raw Zigbee frame.
    Numeric output remains in the original validated unit, without calibration.
    """
    if not isinstance(state, dict) or not isinstance(mapping, dict):
        raise ValueError('invalid_input')
    if not isinstance(instance_id, str) or not instance_id.strip():
        raise ValueError('instance_required')
    entity = mapping.get('entity_id')
    if not isinstance(entity, str) or not re.fullmatch(r'sensor\.[a-z0-9_]+', entity):
        raise ValueError('invalid_entity')
    if state.get('entity_id') != entity:
        raise ValueError('unmapped_entity')
    for field in ('device_id', 'model'):
        if not isinstance(mapping.get(field), str) or not mapping[field].strip():
            raise ValueError('device_mapping_required')
    validate_device_profile(mapping)
    metric = mapping.get('metric')
    if metric not in UNITS:
        raise ValueError('unsupported_metric')
    if type(max_age_seconds) is not int or max_age_seconds <= 0:
        raise ValueError('invalid_age_limit')
    raw = json.dumps(state, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(',', ':'))
    if len(raw.encode('utf-8')) > 65536:
        raise ValueError('state_too_large')
    received = utc(received_at)
    updated = utc(state['last_updated']) if state.get('last_updated') is not None else None
    quality = 'state_time_unknown'
    if updated:
        age = (datetime.fromisoformat(received) - datetime.fromisoformat(updated)).total_seconds()
        quality = 'future_state' if age < -300 else ('stale_state' if age > max_age_seconds else 'recent_state')
    value = state.get('state')
    status = value if value in ('unavailable', 'unknown') else 'available'
    number = None
    unit = None
    if status == 'available':
        attributes = state.get('attributes')
        if not isinstance(attributes, dict):
            raise ValueError('invalid_attributes')
        unit = attributes.get('unit_of_measurement')
        # HA commonly exposes illuminance as lx; lux is equivalent, preserved as received.
        allowed = (UNITS[metric], 'lux') if metric == 'illuminance' else (UNITS[metric],)
        if unit not in allowed:
            raise ValueError('unit_mismatch')
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ValueError('invalid_value')
        try:
            numeric = Decimal(str(value))
        except InvalidOperation:
            raise ValueError('invalid_value') from None
        if not numeric.is_finite():
            raise ValueError('invalid_value')
        if metric in ('soil_moisture', 'air_humidity') and not 0 <= numeric <= 100:
            raise ValueError('invalid_value')
        if metric == 'illuminance' and numeric < 0:
            raise ValueError('invalid_value')
        number = str(numeric)
    record = {
        'schema_version': 1, 'source': 'home_assistant', 'instance_id': instance_id,
        'entity_id': entity, 'device_id': mapping['device_id'], 'model': mapping['model'],
        'metric': metric, 'value': number, 'unit': unit, 'status': status,
        'received_at': received, 'ha_updated_at': updated, 'state_time_quality': quality,
        'measured_at': None, 'measurement_time_quality': 'unknown',
        'calibration': None, 'raw_level': 'home_assistant_state', 'raw_state': json.loads(raw),
        'eligible_for_plant_history': False,
    }
    if mapping.get('hardware_id'):
        from sensor_source_policy import hardware_id
        record['hardware_id'] = hardware_id(mapping['hardware_id'])
    if 'test_data' in mapping:
        record['test_data'] = mapping['test_data']
    # Receipt time is not identity: polling a cached state must not add measurements.
    identity = {k: v for k, v in record.items() if k not in ('received_at', 'state_time_quality')}
    record['observation_id'] = 'ha1_' + hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(',', ':')).encode()).hexdigest()
    return record


def archive_states(path, items, *, instance_id, received_at, max_age_seconds=7200):
    """Opt-in staging DB only; validate the whole batch before opening SQLite.

    Caller supplies (state, mapping) pairs. No default production path exists.
    Unchanged cached states are deduplicated; changed payloads remain available.
    """
    records = [prepare(state, mapping, instance_id=instance_id, received_at=received_at,
                       max_age_seconds=max_age_seconds) for state, mapping in items]
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS ha_states_v1 (observation_id TEXT PRIMARY KEY, record_json TEXT NOT NULL)')
        added = 0
        for record in records:
            added += db.execute('INSERT OR IGNORE INTO ha_states_v1 VALUES (?, ?)',
                                (record['observation_id'], json.dumps(record, ensure_ascii=False, allow_nan=False))).rowcount
    return {'added': added, 'duplicates': len(records) - added}
