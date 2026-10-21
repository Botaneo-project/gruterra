"""Fictional demo remains useful without reading installation secrets."""
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))

class RecoveryDemoTests(unittest.TestCase):
    def test_history_is_fictional_and_has_timeline_missing_zero_and_burst(self):
        from home_assistant_demo import history
        from home_assistant_chart import chart_data
        with patch.dict(os.environ,{'BOTANEO_DEMO':'1'}),patch('home_assistant_ui.load',side_effect=AssertionError('secret')),patch('home_assistant_view.read_rows',side_effect=AssertionError('real archive')):
            rows=history('2026-10-20T08:00:00+00:00')
        self.assertEqual(len(rows),49)
        self.assertTrue(all(row['test_data'] for row in rows))
        self.assertEqual({row['metric'] for row in rows},{'soil_moisture','air_humidity','temperature','illuminance'})
        self.assertTrue(any(row['metric']=='illuminance' and row['value']=='0' for row in rows))
        self.assertTrue(any(row['metric']=='air_humidity' and row['value'] is None for row in rows))
        self.assertGreater(len({row['ha_updated_at'] for row in rows}),10)
        self.assertTrue(all(row['usable_for_timeline'] for row in rows if row['value'] is not None))

if __name__=='__main__':unittest.main()
