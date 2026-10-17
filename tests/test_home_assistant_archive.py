from contextlib import closing
import copy
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_archive import commit_history, checkpoint
from home_assistant_sensors import prepare

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.plants = Path(self.tmp.name)/'plants.db'
        self.archive = Path(self.tmp.name)/'history.sqlite3'
        with closing(sqlite3.connect(self.plants)) as db, db:
            db.execute('CREATE TABLE capteurs (adresse_ble TEXT)')
        self.mapping = {'entity_id': 'sensor.fictitious_lux', 'device_id': 'fictitious', 'model': 'fictitious', 'metric': 'illuminance', 'hardware_id': 'zigbee:0011223344556677', 'hardware_confirmed': True}
        self.config = {'schema_version': 1, 'enabled': True, 'base_url': 'https://example.invalid', 'access_token': 'fictitious-token', 'instance_id': 'fictitious', 'entities': [self.mapping]}
        self.batch = {'ok': True, 'http_status': 200, 'start': '2026-10-15T00:00:00Z', 'end': '2026-10-15T06:00:00Z', 'records': [self.record()]}
    def record(self, value='0', entity=None):
        mapping = self.mapping if entity is None else {**self.mapping, 'entity_id': entity}
        return prepare({'entity_id': mapping['entity_id'], 'state': value, 'attributes': {'unit_of_measurement': 'lx'}, 'last_updated': '2026-10-15T01:00:00Z'}, mapping, instance_id='fictitious', received_at='2026-10-15T07:00:00Z')
    def commit(self, batch=None, config=None):
        return commit_history(self.archive, config or self.config, batch or self.batch, plant_db_path=self.plants)
    def test_durable_commit_and_lost_ack_replay(self):
        first = self.commit()
        second = self.commit()
        self.assertEqual(first['facts_added'], 1)
        self.assertEqual(second['facts_added'], 0)
        self.assertEqual(second['duplicates'], 1)
        self.assertEqual(first['receipt'], second['receipt'])
        self.assertEqual(second['checkpoint'], '2026-10-15T06:00:00+00:00')
    def test_malformed_batch_never_advances(self):
        self.commit()
        before = checkpoint(self.archive, self.config, plant_db_path=self.plants)
        invalid = copy.deepcopy(self.batch)
        invalid['records'].append({**invalid['records'][0], 'value': '100'})
        with self.assertRaises(ValueError):
            self.commit(invalid)
        self.assertEqual(checkpoint(self.archive, self.config, plant_db_path=self.plants), before)
    def test_rollback_on_sql_write_failure(self):
        self.commit()
        with closing(sqlite3.connect(self.archive)) as db, db:
            db.execute("CREATE TRIGGER fail_cursor BEFORE INSERT ON ha_cursor_v1 BEGIN SELECT RAISE(ABORT,'simulated'); END")
        next_batch = {**self.batch, 'start': self.batch['end'], 'end': '2026-10-15T12:00:00Z', 'records': []}
        with self.assertRaises(sqlite3.DatabaseError):
            self.commit(next_batch)
        self.assertEqual(checkpoint(self.archive, self.config, plant_db_path=self.plants), '2026-10-15T06:00:00+00:00')
        with closing(sqlite3.connect(self.archive)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM ha_windows_v1').fetchone()[0], 1)
    def test_gap_refused_and_empty_response_not_physical_proof(self):
        self.commit()
        with self.assertRaisesRegex(ValueError, 'history_gap'):
            self.commit({**self.batch, 'start': '2026-10-15T07:00:00Z', 'end': '2026-10-15T12:00:00Z', 'records': []})
        result = self.commit({**self.batch, 'start': self.batch['end'], 'end': '2026-10-15T12:00:00Z', 'records': []})
        self.assertEqual(result['coverage'], 'ha_response_staged_only')
        self.assertFalse(result['eligible_for_plant_history'])
    def test_plant_database_forbidden_unchanged(self):
        before = self.plants.read_bytes()
        with self.assertRaisesRegex(ValueError, 'plant_database_forbidden'):
            commit_history(self.plants, self.config, self.batch, plant_db_path=self.plants)
        self.assertEqual(self.plants.read_bytes(), before)
    def test_alias_does_not_duplicate_physical_fact(self):
        self.commit()
        config = {**self.config, 'entities': [{**self.mapping, 'entity_id': 'sensor.renamed'}]}
        result = self.commit({**self.batch, 'records': [self.record('0.0', 'sensor.renamed')]}, config)
        self.assertEqual(result['facts_added'], 0)
        self.assertEqual(result['revisions_added'], 0)
        self.assertEqual(result['envelopes_added'], 1)
    def test_correction_preserved_as_revision(self):
        self.commit()
        result = self.commit({**self.batch, 'records': [self.record('15')]})
        self.assertEqual(result['facts_added'], 0)
        self.assertEqual(result['revisions_added'], 1)
    def test_new_bluetooth_registration_blocks_pending_batch(self):
        config = {**self.config, 'entities': [{**self.mapping, 'hardware_id': 'ble:11:22:33:44:55:66'}]}
        with closing(sqlite3.connect(self.plants)) as db, db:
            db.execute('INSERT INTO capteurs VALUES (?)', ('11:22:33:44:55:66',))
        with self.assertRaisesRegex(ValueError, 'mapping_not_authorized'):
            self.commit(config=config)
        self.assertFalse(self.archive.exists())

if __name__ == '__main__':
    unittest.main()
