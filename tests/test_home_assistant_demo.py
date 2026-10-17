from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
import home_assistant_client as client
from home_assistant_history import read_history
from home_assistant_registry import preview
from home_assistant_demo import preview as fictional_preview

class DemoTests(unittest.TestCase):
    def test_demo_entry_points_block_before_network_and_private_config(self):
        with patch.dict('os.environ', {'BOTANEO_DEMO':'1'}), patch('home_assistant_secrets.read_private', side_effect=AssertionError('private access')):
            fake = lambda *a,**k:self.fail('network')
            results = [client.read_snapshot({}, received_at='2026-10-16T10:00:00Z', requester=fake),
                       client.read_configured_snapshot('unused', received_at='2026-10-16T10:00:00Z', requester=fake),
                       preview({}, [], received_at='2026-10-16T10:00:00Z', requester=fake),
                       read_history({}, owners={}, existing_ble_addresses=[], start='2026-10-16T00:00:00Z', end='2026-10-16T06:00:00Z', received_at='2026-10-16T10:00:00Z', requester=fake)]
            for result in results:
                self.assertEqual(result['code'], 'demo_disabled')
    def test_fictional_example_preserves_zero_and_unavailable(self):
        with patch('requests.Session', side_effect=AssertionError('network')):
            result = fictional_preview('2026-10-16T10:00:00Z')
        self.assertTrue(result['demo'])
        self.assertEqual(len(result['records']), 4)
        light = next(row for row in result['records'] if row['metric']=='illuminance')
        missing = next(row for row in result['records'] if row['status']=='unavailable')
        self.assertEqual(light['value'], '0')
        self.assertIsNone(missing['value'])
        self.assertTrue(all(not row['eligible_for_plant_history'] for row in result['records']))

if __name__=='__main__':
    unittest.main()
