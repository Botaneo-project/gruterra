import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_sensors import prepare, archive_states

class HomeAssistantTests(unittest.TestCase):
    def setUp(self):
        self.state = {'entity_id': 'sensor.test_lux', 'state': '0', 'last_updated': '2026-10-15T09:00:00Z', 'attributes': {'unit_of_measurement': 'lx'}}
        self.mapping = {'entity_id': 'sensor.test_lux', 'device_id': 'fictitious-device', 'model': 'fictitious-model', 'metric': 'illuminance'}
        self.args = {'instance_id': 'test-instance', 'received_at': '2026-10-15T09:01:00Z'}
    def test_zero_provenance_and_unknown_physical_time(self):
        r = prepare(self.state, self.mapping, **self.args)
        self.assertEqual(r['value'], '0')
        self.assertEqual(r['raw_state'], self.state)
        self.assertEqual(r['state_time_quality'], 'recent_state')
        self.assertIsNone(r['measured_at'])
        self.assertFalse(r['eligible_for_plant_history'])
    def test_cached_poll_does_not_create_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stage.sqlite3'
            self.assertEqual(archive_states(path, [(self.state, self.mapping)], **self.args)['added'], 1)
            args = {**self.args, 'received_at': '2026-10-15T15:00:00Z'}
            self.assertEqual(archive_states(path, [(self.state, self.mapping)], **args), {'added': 0, 'duplicates': 1})
    def test_unavailable_and_unknown_are_not_zero(self):
        for status in ('unavailable', 'unknown'):
            r = prepare({**self.state, 'state': status}, self.mapping, **self.args)
            self.assertEqual(r['status'], status)
            self.assertIsNone(r['value'])
    def test_old_future_and_missing_state_dates(self):
        for time, expected in [('2026-10-14T09:00:00Z', 'stale_state'), ('2026-10-16T09:00:00Z', 'future_state'), (None, 'state_time_unknown')]:
            r = prepare({**self.state, 'last_updated': time}, self.mapping, **self.args)
            self.assertEqual(r['state_time_quality'], expected)
    def test_wrong_entity_units_values_and_naive_dates(self):
        for change in ({'entity_id': 'sensor.other'}, {'attributes': {'unit_of_measurement': '%'}}, {'state': 'NaN'}, {'state': '-1'}, {'state': True}, {'last_updated': '2026-10-15T09:00:00'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                prepare({**self.state, **change}, self.mapping, **self.args)
    def test_air_and_soil_humidity_are_distinct(self):
        state = {**self.state, 'state': '30', 'attributes': {'unit_of_measurement': '%'}}
        a = prepare(state, {**self.mapping, 'metric': 'air_humidity'}, **self.args)
        b = prepare(state, {**self.mapping, 'metric': 'soil_moisture'}, **self.args)
        self.assertNotEqual(a['observation_id'], b['observation_id'])
        with self.assertRaises(ValueError):
            prepare({**state, 'state': '101'}, {**self.mapping, 'metric': 'soil_moisture'}, **self.args)
    def test_invalid_batch_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stage.sqlite3'
            with self.assertRaises(ValueError):
                archive_states(path, [(self.state, self.mapping), ({**self.state, 'state': 'bad'}, self.mapping)], **self.args)
            self.assertFalse(path.exists())
    def test_revised_payload_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stage.sqlite3'
            archive_states(path, [(self.state, self.mapping), ({**self.state, 'state': '20'}, self.mapping)], **self.args)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM ha_states_v1').fetchone()[0], 2)

if __name__ == '__main__':
    unittest.main()
