"""Fictional HA preview, no configuration, credentials or networking."""
from datetime import datetime, timedelta, timezone
from home_assistant_sensors import prepare


def preview(now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    rows = []
    for name, metric, value, unit in [('soil', 'soil_moisture', '28', '%'),
                                      ('temperature', 'temperature', '22.5', '°C'),
                                      ('light', 'illuminance', '0', 'lx'),
                                      ('air', 'air_humidity', 'unavailable', '%')]:
        entity = 'sensor.demo_'+name
        mapping = {'entity_id': entity, 'device_id': 'fictional-demo-device', 'model': 'ZS-304Z', 'metric': metric,
                   'hardware_id': 'zigbee:0011223344556677', 'test_data': True}
        state = {'entity_id': entity, 'state': value, 'attributes': {'unit_of_measurement': unit}, 'last_updated': now}
        rows.append(prepare(state, mapping, instance_id='fictional-demo-ha', received_at=now))
    return {'ok': True, 'code': 'demo_ready', 'http_status': None, 'demo': True, 'records': rows}


def history(now=None):
    """Fictional timeline for the dashboard; no private config or archive access."""
    from home_assistant_timing import timing
    instant = datetime.fromisoformat(now) if now else datetime.now(timezone.utc)
    rows = []
    for index in range(12):
        stamp = (instant-timedelta(hours=11-index)).isoformat()
        for original in preview(stamp)['records']:
            mapping = {'entity_id': original['entity_id'], 'device_id': 'fictional-demo-device',
                       'model': 'ZS-304Z', 'metric': original['metric'],
                       'hardware_id': original['hardware_id'], 'test_data': True}
            metric = mapping['metric']
            value = {'soil_moisture': str(28-index/2), 'temperature': str(22+index/10),
                     'illuminance': str(max(0, (index-5)*120)),
                     'air_humidity': 'unavailable' if index==6 else str(55+index%3)}[metric]
            state = {**original['raw_state'], 'state': value, 'last_changed': stamp,
                     'last_updated': stamp}
            record = prepare(state, mapping, instance_id='fictional-demo-ha', received_at=instant.isoformat())
            rows.append({**record, **timing(record), 'versions': 1})
            if metric == 'soil_moisture' and index == 8:
                # Illustrate a contradictory burst without averaging its values.
                second = (datetime.fromisoformat(stamp)+timedelta(milliseconds=200)).isoformat()
                record = prepare({**state, 'state': '18', 'last_changed': second, 'last_updated': second},
                                 mapping, instance_id='fictional-demo-ha', received_at=instant.isoformat())
                rows.append({**record, **timing(record), 'versions': 1})
    return sorted(rows, key=lambda row: row['ha_updated_at'], reverse=True)
