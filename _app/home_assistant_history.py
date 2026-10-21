"""Bounded, opt-in history reads; no scheduler or plant DB writes."""
import json
from datetime import datetime
from urllib.parse import quote
from home_assistant_client import validate_config, _unique_object
from home_assistant_sensors import prepare, utc
from sensor_source_policy import authorize_ha_mappings

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 10000


def decode_history(payload, mappings, *, instance_id, start, end, received_at):
    """Exclude initial carry-in states; never turn HA time into sensor time."""
    begin, stop = datetime.fromisoformat(utc(start)), datetime.fromisoformat(utc(end))
    if not 0 < (stop-begin).total_seconds() <= 21600:
        raise ValueError('invalid_history_window')
    if not isinstance(payload, list):
        raise ValueError('invalid_history')
    mapping = {item['entity_id']: item for item in mappings}
    items, ids = [], set()
    total = 0
    for group in payload:
        if not isinstance(group, list):
            raise ValueError('invalid_history')
        for state in group:
            total += 1
            if total > MAX_ROWS:
                raise ValueError('history_too_large')
            if not isinstance(state, dict) or state.get('entity_id') not in mapping:
                raise ValueError('unmapped_history_entity')
            # Do not accept minimal responses: they can omit identity/attributes.
            updated = datetime.fromisoformat(utc(state.get('last_updated')))
            if not begin <= updated < stop:
                continue
            record = prepare(state, mapping[state['entity_id']], instance_id=instance_id,
                             received_at=received_at)
            if record['observation_id'] not in ids:
                ids.add(record['observation_id'])
                items.append(record)
    return sorted(items, key=lambda record: (record['ha_updated_at'], record['entity_id'], record['observation_id']))


def read_history(config, *, owners, existing_ble_addresses, start, end, received_at, requester=None):
    if __import__('os').environ.get('BOTANEO_DEMO') == '1':
        return {'ok': False, 'code': 'demo_disabled', 'http_status': None, 'records': []}
    session = response = None
    try:
        base, token, mappings = validate_config(config)
        authorize_ha_mappings(mappings, owners, existing_ble_addresses=existing_ble_addresses)
        # Validate interval and timestamps before issuing any request.
        decode_history([], mappings, instance_id=config['instance_id'], start=start, end=end, received_at=received_at)
        utc(received_at)
        if requester is None:
            import requests
            session = requests.Session()
            session.trust_env = False
            requester = session.get
        response = requester(base+'/api/history/period/'+quote(utc(start), safe=''),
                             params={'filter_entity_id': ','.join(item['entity_id'] for item in mappings), 'end_time': utc(end),
                                     'skip_initial_state': 'true', 'significant_changes_only': '0'},
                             headers={'Authorization': 'Bearer '+token, 'Accept': 'application/json'},
                             timeout=(5, 30), allow_redirects=False, stream=True)
        if response.status_code != 200:
            return {'ok': False, 'code': 'history_http_error', 'http_status': response.status_code, 'records': []}
        body = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            body.extend(chunk)
            if len(body) > MAX_BYTES:
                raise ValueError('history_too_large')
        payload = json.loads(body.decode('utf-8'), object_pairs_hook=_unique_object,
                             parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid_history')))
        records = decode_history(payload, mappings, instance_id=config['instance_id'], start=start, end=end, received_at=received_at)
        return {'ok': True, 'code': 'history_ready' if records else 'history_empty',
                'http_status': 200, 'records': records, 'start': utc(start), 'end': utc(end),
                'physical_measurements_confirmed': False}
    except ValueError as error:
        safe = {'disabled', 'physical_identity_required', 'source_not_authorized', 'duplicate_physical_measurement', 'invalid_source_policy', 'invalid_history_window', 'history_too_large', 'unmapped_history_entity'}
        return {'ok': False, 'code': str(error) if str(error) in safe else 'invalid_history', 'http_status': None, 'records': []}
    except Exception:
        return {'ok': False, 'code': 'history_connection_failed', 'http_status': None, 'records': []}
    finally:
        if response is not None:
            response.close()
        if session is not None:
            session.close()
