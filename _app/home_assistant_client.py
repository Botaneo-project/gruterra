"""Opt-in read-only Home Assistant client. Not wired into the running app."""
import ipaddress
import json
import re
from urllib.parse import urlsplit
from home_assistant_sensors import prepare

MAX_RESPONSE = 65536


def validate_config(config):
    if not isinstance(config, dict) or config.get('enabled') is not True:
        raise ValueError('disabled')
    if config.get('schema_version') != 1:
        raise ValueError('invalid_config')
    url = config.get('base_url')
    if not isinstance(url, str):
        raise ValueError('invalid_url')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError('invalid_url')
    try:
        parsed.port
    except ValueError:
        raise ValueError('invalid_url') from None
    # Plain HTTP only for explicitly selected private IPs or localhost.
    if parsed.scheme == 'http':
        try:
            address = ipaddress.ip_address(parsed.hostname)
            local = address.is_private or address.is_loopback
        except ValueError:
            local = parsed.hostname == 'localhost'
        if not local:
            raise ValueError('https_required')
    token = config.get('access_token')
    if not isinstance(token, str) or not token or len(token) > 8192 or any(c.isspace() for c in token):
        raise ValueError('invalid_credentials')
    instance = config.get('instance_id')
    if not isinstance(instance, str) or not instance.strip():
        raise ValueError('instance_required')
    mappings = config.get('entities')
    if not isinstance(mappings, list) or not 1 <= len(mappings) <= 100:
        raise ValueError('entities_required')
    seen = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise ValueError('invalid_mapping')
        entity = mapping.get('entity_id')
        if not isinstance(entity, str) or not re.fullmatch(r'sensor\.[a-z0-9_]+', entity) or entity in seen:
            raise ValueError('invalid_mapping')
        seen.add(entity)
        # Validate the entire mapping before any network request.
        prepare({'entity_id': entity, 'state': 'unknown'}, mapping,
                instance_id=instance, received_at='2000-01-01T00:00:00Z',
                max_age_seconds=config.get('max_state_age_seconds', 7200))
    return url.rstrip('/'), token, mappings


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('invalid_response')
        value[key] = item
    return value


def read_snapshot(config, *, received_at, requester=None):
    """Return a fully validated snapshot, never a success with partial states.

    Errors contain fixed safe codes only. No raw exceptions, bodies or headers.
    This reads current HA states; it does not retrieve missed measurement history.
    """
    if __import__('os').environ.get('BOTANEO_DEMO') == '1':
        return {'ok': False, 'code': 'demo_disabled', 'http_status': None, 'records': []}
    session = None
    try:
        base, token, mappings = validate_config(config)
        if requester is None:
            import requests
            session = requests.Session()
            session.trust_env = False
            requester = session.get
        records = []
        for mapping in mappings:
            response = None
            try:
                response = requester(base + '/api/states/' + mapping['entity_id'],
                                     headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'},
                                     timeout=(5, 15), allow_redirects=False, stream=True)
                status = response.status_code
                if status != 200:
                    code = {401: 'unauthorized', 403: 'forbidden', 404: 'entity_not_found', 429: 'rate_limited'}.get(status, 'http_error')
                    return {'ok': False, 'code': code, 'http_status': status, 'records': []}
                body = bytearray()
                for chunk in response.iter_content(chunk_size=8192):
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE:
                        raise ValueError('response_too_large')
                state = json.loads(body.decode('utf-8'), object_pairs_hook=_unique_object,
                                   parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid_response')))
                records.append(prepare(state, mapping, instance_id=config['instance_id'],
                                       received_at=received_at, max_age_seconds=config.get('max_state_age_seconds', 7200)))
            finally:
                if response is not None:
                    response.close()
        return {'ok': True, 'code': 'snapshot_ready', 'http_status': 200, 'records': records}
    except ValueError as error:
        allowed = {'disabled', 'invalid_config', 'invalid_url', 'https_required', 'invalid_credentials', 'instance_required', 'entities_required', 'invalid_mapping', 'response_too_large'}
        code = str(error) if str(error) in allowed else 'invalid_state_or_response'
        return {'ok': False, 'code': code, 'http_status': None, 'records': []}
    except Exception:
        return {'ok': False, 'code': 'connection_failed', 'http_status': None, 'records': []}
    finally:
        if session is not None:
            session.close()


def read_configured_snapshot(path, *, received_at, requester=None):
    """Decrypt locally for an explicitly requested read; never expose disk config."""
    if __import__('os').environ.get('BOTANEO_DEMO') == '1':
        return {'ok': False, 'code': 'demo_disabled', 'http_status': None, 'records': []}
    try:
        from home_assistant_secrets import read_private
        config = read_private(path)
        if config.get('_secret_unavailable'):
            return {'ok': False, 'code': 'secret_unavailable', 'http_status': None, 'records': []}
        return read_snapshot(config, received_at=received_at, requester=requester)
    except Exception:
        return {'ok': False, 'code': 'private_config_unavailable', 'http_status': None, 'records': []}
