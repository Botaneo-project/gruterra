"""Fictional HA preview, no configuration, credentials or networking."""
from datetime import datetime, timezone
from home_assistant_sensors import prepare


def preview(now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    rows = []
    for name, metric, value, unit in [('soil', 'soil_moisture', '28', '%'),
                                      ('temperature', 'temperature', '22.5', '°C'),
                                      ('light', 'illuminance', '0', 'lx'),
                                      ('air', 'air_humidity', 'unavailable', '%')]:
        entity = 'sensor.demo_'+name
        mapping = {'entity_id': entity, 'device_id': 'fictional-demo-device', 'model': 'Fictional demo sensor', 'metric': metric}
        state = {'entity_id': entity, 'state': value, 'attributes': {'unit_of_measurement': unit}, 'last_updated': now}
        rows.append(prepare(state, mapping, instance_id='fictional-demo-ha', received_at=now))
    return {'ok': True, 'code': 'demo_ready', 'http_status': None, 'demo': True, 'records': rows}
