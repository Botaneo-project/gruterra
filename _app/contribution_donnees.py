"""Contrat de contenu V2, sans transport, identité ni consentement.

Portage du validateur du prototype, conformément à CONTRAT_DONNEES_V2.md.
"""
import json
import math
import re
from i18n import traduire_courant as t


def valider_contribution_v2(payload):
    def fail():
        raise ValueError(t('contribution_data_invalid'))

    def fields(item, allowed, required):
        if type(item) is not dict or set(item) - set(allowed) or set(required) - set(item):
            fail()
        if any(value is None for value in item.values()):
            fail()

    fields(payload, ['schema_version', 'plants', 'measurements', 'events'],
           ['schema_version', 'plants', 'measurements', 'events'])
    if type(payload['schema_version']) is not int or payload['schema_version'] != 2:
        fail()
    for key, maximum in [('plants', 100), ('measurements', 10000), ('events', 2000)]:
        if type(payload[key]) is not list or len(payload[key]) > maximum:
            fail()
    refs = set()
    for plant in payload['plants']:
        fields(plant, ['plant_ref'], ['plant_ref'])
        ref = plant['plant_ref']
        if type(ref) is not str or not re.fullmatch(r'p[1-9][0-9]{0,5}', ref) or ref in refs:
            fail()
        refs.add(ref)
    used, unique = set(), set()
    ranges = {'moisture_pct': (0, 100, 0), 'illuminance_lux': (0, 10000000, 0),
              'temperature_c': (-273.1, 1000, 1), 'conductivity_us_cm': (0, 10000000, 0)}
    for group in ['measurements', 'events']:
        for item in payload[group]:
            required = ['plant_ref', 'elapsed_hour', 'elapsed_second']
            allowed = required + list(ranges)
            if group == 'events':
                required += ['event_type']
                allowed = required + ['water_volume_ml']
            fields(item, allowed, required)
            ref, hour = item['plant_ref'], item['elapsed_hour']
            if type(ref) is not str or ref not in refs or type(hour) is not int or not 0 <= hour <= 876000:
                fail()
            second = item['elapsed_second']
            if type(second) is not int or not 0 <= second <= 3153603599 or second // 3600 != hour:
                fail()
            time_key = second
            used.add(ref)
            if group == 'measurements':
                if (ref, time_key) in unique or not set(item).intersection(ranges):
                    fail()
                unique.add((ref, time_key))
                for key, (low, high, decimals) in ranges.items():
                    if key not in item:
                        continue
                    value = item[key]
                    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
                        fail()
                    if abs(value - round(value, decimals)) > 0.000001:
                        fail()
            else:
                if item['event_type'] != 'watering':
                    fail()
                if 'water_volume_ml' in item:
                    volume = item['water_volume_ml']
                    if type(volume) not in (int, float) or not 0 < volume <= 10000000 or not math.isfinite(volume):
                        fail()
    if not refs or used != refs:
        fail()
    if len(json.dumps(payload, ensure_ascii=False).encode('utf-8')) > 1048576:
        fail()
    return payload
