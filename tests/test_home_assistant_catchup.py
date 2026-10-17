from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_catchup import plan_catchup, run_catchup
from home_assistant_archive import checkpoint

class CatchupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.plants = Path(self.tmp.name)/'plants.db'
        self.archive = Path(self.tmp.name)/'ha.sqlite3'
        with closing(sqlite3.connect(self.plants)) as db, db:
            db.execute('CREATE TABLE capteurs (adresse_ble TEXT)')
        self.config = {'schema_version': 1, 'enabled': False, 'base_url': 'https://example.invalid', 'access_token': 'fictitious', 'instance_id': 'fictitious', 'entities': [{'entity_id': 'sensor.fictitious', 'device_id': 'fictitious', 'model': 'fictitious', 'metric': 'illuminance', 'hardware_id': 'zigbee:0011223344556677', 'hardware_confirmed': True}]}
        self.times = {'start': '2026-10-15T00:00:00Z', 'end': '2026-10-15T12:00:00Z', 'received_at': '2026-10-15T13:00:00Z'}
    def plan(self, **kwargs):
        return plan_catchup(self.config, self.archive, plant_db_path=self.plants, **{**self.times, **kwargs})
    def execute(self, plan, **kwargs):
        return run_catchup(self.config, plan, self.archive, plant_db_path=self.plants, received_at=self.times['received_at'], **kwargs)
    def response(self, status=200):
        class Response:
            status_code = status
            def iter_content(inner, chunk_size):
                yield b'[]'
            def close(inner):
                pass
        return Response()
    def test_plan_and_missing_confirmation_never_create_archive(self):
        plan = self.plan()
        self.assertEqual(len(plan['windows']), 2)
        self.assertFalse(self.archive.exists())
        result = self.execute(plan, requester=lambda *a, **k: self.fail('network'))
        self.assertEqual(result['code'], 'confirmation_required')
        self.assertFalse(self.archive.exists())
    def test_full_catchup_keeps_disabled_and_does_not_touch_plants(self):
        before = self.plants.read_bytes()
        result = self.execute(self.plan(), confirmed=True, requester=lambda *a, **k: self.response())
        self.assertTrue(result['ok'])
        self.assertEqual(result['completed_windows'], 2)
        self.assertFalse(result['retention_verified'])
        self.assertFalse(self.config['enabled'])
        self.assertEqual(self.plants.read_bytes(), before)
        self.assertEqual(len(self.plan()['windows']), 0)
    def test_network_failure_resumes_at_last_committed_window(self):
        responses = iter([self.response(), self.response(503)])
        result = self.execute(self.plan(), confirmed=True, requester=lambda *a, **k: next(responses))
        self.assertFalse(result['ok'])
        self.assertEqual(result['completed_windows'], 1)
        self.assertEqual(checkpoint(self.archive, self.config, plant_db_path=self.plants), '2026-10-15T06:00:00+00:00')
        plan = self.plan()
        self.assertEqual(len(plan['windows']), 1)
        self.assertTrue(self.execute(plan, confirmed=True, requester=lambda *a, **k: self.response())['ok'])
    def test_changed_mapping_or_plan_refused_before_network(self):
        plan = self.plan()
        plan['windows'] = []
        result = self.execute(plan, confirmed=True, requester=lambda *a, **k: self.fail('network'))
        self.assertEqual(result['code'], 'plan_changed')
        self.assertFalse(self.archive.exists())
    def test_demo_refused(self):
        with patch.dict('os.environ', {'BOTANEO_DEMO': '1'}):
            with self.assertRaisesRegex(ValueError, 'demo_disabled'):
                self.plan()
    def test_four_windows_max_and_range_cannot_skip_checkpoint(self):
        plan = self.plan(start='2026-10-14T00:00:00Z')
        self.assertEqual(len(plan['windows']), 4)
        self.assertTrue(plan['more_pending'])
        self.execute(self.plan(), confirmed=True, requester=lambda *a, **k: self.response())
        with self.assertRaisesRegex(ValueError, 'requested_range_skips_checkpoint'):
            self.plan(start='2026-10-15T12:30:00Z', end='2026-10-15T13:00:00Z')

if __name__ == '__main__':
    unittest.main()
