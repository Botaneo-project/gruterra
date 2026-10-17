from pathlib import Path
from contextlib import closing
import sys
import sqlite3
import tempfile
import unittest
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_registry import assess_mappings, authorized_selection, preview

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'plants.db'
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE capteurs (adresse_ble TEXT)')
            db.execute('INSERT INTO capteurs VALUES (?)', ('AA:BB:CC:DD:EE:FF',))
        self.row = {'entity_id': 'sensor.fictitious_lux', 'device_id': 'fictitious', 'model': 'fictitious', 'metric': 'illuminance', 'hardware_id': 'zigbee:0011223344556677', 'hardware_confirmed': True}
    def test_existing_miflora_blocked_regardless_of_name(self):
        row = {**self.row, 'hardware_id': 'ble:aa-bb-cc-dd-ee-ff', 'device_id': 'different-name'}
        self.assertEqual(assess_mappings([row], db_path=self.path), ['already_ble'])
        with self.assertRaises(ValueError):
            authorized_selection([row], db_path=self.path)
    def test_unknown_identity_and_unconfirmed_never_authorized(self):
        self.assertEqual(assess_mappings([{**self.row, 'hardware_id': ''}, {**self.row, 'hardware_confirmed': False}], db_path=self.path), ['identity_pending', 'identity_pending'])
    def test_device_quantity_aliases_blocked_but_distinct_devices_kept(self):
        other = {**self.row, 'entity_id': 'sensor.alias'}
        self.assertEqual(assess_mappings([self.row, other], db_path=self.path), ['duplicate', 'duplicate'])
        other['hardware_id'] = 'zigbee:0011223344556688'
        self.assertEqual(assess_mappings([self.row, other], db_path=self.path), ['authorized', 'authorized'])
    def test_db_unavailable_blocks_before_network(self):
        missing = self.path.parent / 'missing.db'
        self.assertEqual(assess_mappings([self.row], db_path=missing), ['registry_unavailable'])
        result = preview({}, [self.row], received_at='2026-10-15T10:00:00Z', db_path=missing, requester=lambda *a, **k: self.fail('network'))
        self.assertFalse(result['ok'])
        self.assertFalse(missing.exists())
    def test_current_registry_rechecked_and_no_database_mutation(self):
        owners, ble = authorized_selection([self.row], db_path=self.path)
        self.assertEqual(list(owners.values()), ['home_assistant'])
        self.assertEqual(ble, ['aabbccddeeff'])
        row = {**self.row, 'hardware_id': 'ble:11:22:33:44:55:66'}
        self.assertEqual(assess_mappings([row], db_path=self.path), ['authorized'])
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT INTO capteurs VALUES (?)', ('11:22:33:44:55:66',))
        self.assertEqual(assess_mappings([row], db_path=self.path), ['already_ble'])
    def test_preview_success_has_no_archive_or_db_write(self):
        before = self.path.read_bytes()
        config = {'schema_version': 1, 'enabled': False, 'base_url': 'https://example.invalid', 'access_token': 'fictitious', 'instance_id': 'fictitious'}
        state = {'entity_id': self.row['entity_id'], 'state': '0', 'attributes': {'unit_of_measurement': 'lx'}, 'last_updated': '2026-10-15T09:00:00Z'}
        class Response:
            status_code = 200
            def iter_content(inner, chunk_size):
                yield json.dumps(state).encode()
            def close(inner):
                pass
        result = preview(config, [self.row], received_at='2026-10-15T10:00:00Z', db_path=self.path, requester=lambda *a, **k: Response())
        self.assertTrue(result['ok'])
        self.assertEqual(result['records'][0]['value'], '0')
        self.assertFalse(config['enabled'])
        self.assertEqual(self.path.read_bytes(), before)

if __name__ == '__main__':
    unittest.main()
