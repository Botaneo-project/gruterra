"""Explicit physical-device ownership for future multi-source imports.

Sensor display names and similar values are never used as identity evidence.
Existing Mi Flora BLE registrations take precedence over HA ownership claims.
"""
import re


def hardware_id(value):
    if not isinstance(value, str):
        raise ValueError('physical_identity_required')
    prefix, separator, address = value.strip().partition(':')
    if separator != ':' or prefix not in ('ble', 'zigbee'):
        raise ValueError('physical_identity_required')
    cleaned = re.sub(r'[:-]', '', address).lower()
    if cleaned.startswith('0x'):
        cleaned = cleaned[2:]
    size = 12 if prefix == 'ble' else 16
    if not re.fullmatch(r'[0-9a-f]{'+str(size)+'}', cleaned):
        raise ValueError('physical_identity_required')
    return prefix+':'+cleaned


def authorize_ha_mappings(mappings, owners, *, existing_ble_addresses=()):
    """Fail closed unless each physical device is explicitly assigned to HA.

    owners is a local explicit {physical_id: source} registry, not supplied by HA.
    Existing BLE ownership cannot be bypassed by changing the HA display name.
    Several quantities per device are allowed; competing entities for the same
    device and quantity are rejected, even if entity IDs differ.
    """
    if not isinstance(owners, dict) or not isinstance(mappings, list):
        raise ValueError('invalid_source_policy')
    normalized = {}
    for key, source in owners.items():
        physical = hardware_id(key)
        if physical in normalized or source not in ('home_assistant', 'miflora_ble'):
            raise ValueError('invalid_source_policy')
        normalized[physical] = source
    for address in existing_ble_addresses:
        # Existing application BLE registrations are authoritative.
        normalized[hardware_id('ble:'+address)] = 'miflora_ble'
    pairs = set()
    for mapping in mappings:
        physical = hardware_id(mapping.get('hardware_id'))
        if normalized.get(physical) != 'home_assistant':
            raise ValueError('source_not_authorized')
        pair = (physical, mapping.get('metric'))
        if pair in pairs:
            raise ValueError('duplicate_physical_measurement')
        pairs.add(pair)
    return True
