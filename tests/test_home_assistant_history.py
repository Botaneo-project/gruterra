import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_history import decode_history, read_history
from sensor_source_policy import authorize_ha_mappings

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {'entity_id': 'sensor.fictitious_lux', 'device_id': 'fictitious', 'model': 'fictitious', 'metric': 'illuminance', 'hardware_id': 'zigbee:0x0011223344556677'}
        self.owners = {'zigbee:0011223344556677': 'home_assistant'}
        self.config = {'schema_version': 1, 'enabled': True, 'base_url': 'https://example.invalid', 'access_token': 'fictitious-token', 'instance_id': 'fictitious', 'entities': [self.mapping]}
        self.times = {'start': '2026-10-15T00:00:00Z', 'end': '2026-10-15T06:00:00Z', 'received_at': '2026-10-15T07:00:00Z'}
    def state(self, time, value='0'):
        return {'entity_id': self.mapping['entity_id'], 'state': value, 'attributes': {'unit_of_measurement': 'lx'}, 'last_updated': time}
    def decode(self, payload):
        return decode_history(payload, [self.mapping], instance_id='fictitious', **self.times)
    def test_boundaries_carry_in_zero_and_replay(self):
        a = self.state(self.times['start'])
        b = self.state('2026-10-15T05:00:00Z', '10')
        records = self.decode([[self.state('2026-10-14T23:59:00Z'), a, b, a, self.state(self.times['end'])]])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['value'], '0')
        self.assertEqual(records, self.decode([[a, b]]))
        self.assertFalse(records[0]['eligible_for_plant_history'])
    def test_unknown_entity_and_incomplete_timestamps_rejected(self):
        for state in [{**self.state(self.times['start']), 'entity_id': 'sensor.other'}, {**self.state(self.times['start']), 'last_updated': None}]:
            with self.assertRaises(ValueError):
                self.decode([[state]])
    def test_same_value_at_two_times_preserved(self):
        self.assertEqual(len(self.decode([[self.state(self.times['start']), self.state('2026-10-15T01:00:00Z')]])), 2)
    def test_miflora_existing_ble_cannot_be_imported_via_ha(self):
        mapping = {**self.mapping, 'hardware_id': 'ble:AA:BB:CC:DD:EE:FF'}
        with self.assertRaisesRegex(ValueError, 'source_not_authorized'):
            authorize_ha_mappings([mapping], {'ble:aabbccddeeff': 'home_assistant'}, existing_ble_addresses=['AA:BB:CC:DD:EE:FF'])
    def test_two_entities_same_physical_quantity_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_physical_measurement'):
            authorize_ha_mappings([self.mapping, {**self.mapping, 'entity_id': 'sensor.alias'}], self.owners)
        self.assertTrue(authorize_ha_mappings([self.mapping, {**self.mapping, 'entity_id': 'sensor.other', 'metric': 'temperature'}], self.owners))
    def test_unknown_identity_prevents_network(self):
        config = {**self.config, 'entities': [{k: v for k,v in self.mapping.items() if k != 'hardware_id'}]}
        result = read_history(config, owners=self.owners, existing_ble_addresses=[], requester=lambda *a, **k: self.fail('unexpected network'), **self.times)
        self.assertEqual(result['code'], 'physical_identity_required')
    def test_history_request_is_filtered_and_replay_stable(self):
        calls = []
        class Response:
            status_code = 200
            closed = False
            def iter_content(inner, chunk_size):
                yield json.dumps([[self.state(self.times['start'])]]).encode()
            def close(inner):
                inner.closed = True
        response = Response()
        def fake(url, **kwargs):
            calls.append(kwargs)
            return response
        result = read_history(self.config, owners=self.owners, existing_ble_addresses=[], requester=fake, **self.times)
        self.assertTrue(result['ok'])
        self.assertEqual(calls[0]['params']['filter_entity_id'], self.mapping['entity_id'])
        self.assertNotIn('minimal_response', calls[0]['params'])
        self.assertEqual(calls[0]['params']['skip_initial_state'],'true')
        self.assertEqual(calls[0]['params']['significant_changes_only'],'0')
        self.assertFalse(calls[0]['allow_redirects'])
        self.assertTrue(response.closed)
    def test_empty_history_not_claimed_as_physical_data(self):
        self.assertEqual(self.decode([]), [])
        with self.assertRaises(ValueError):
            decode_history([], [self.mapping], instance_id='fictitious', **{**self.times, 'end': '2026-10-16T06:00:00Z'})

if __name__ == '__main__':
    unittest.main()
