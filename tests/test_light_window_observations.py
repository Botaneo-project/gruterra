from datetime import datetime
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from light_window_ui import observation_summary

class ObservationSummaryTests(unittest.TestCase):
    def group(self, points):
        return {'day': '2026-10-15', 'maximum': 500, 'points': points}
    def test_phase_does_not_claim_measurement_completeness(self):
        group = self.group([{'at': '2026-10-15T10:00:00', 'lux': 100}, {'at': '2026-10-15T13:00:00', 'lux': 0}])
        self.assertEqual(observation_summary(group, '09:00', '15:00', datetime(2026,10,15,14))['phase'], 'ongoing')
        result = observation_summary(group, '09:00', '15:00', datetime(2026,10,15,16))
        self.assertEqual(result['phase'], 'ended')
        self.assertEqual(result['largest_gap_seconds'], 10800)
        self.assertEqual(result['last'], datetime(2026,10,15,13))
    def test_single_reading_has_no_invented_gap(self):
        result = observation_summary(self.group([{'at': '2026-10-15T10:00:00', 'lux': 0}]), '09:00','15:00', datetime(2026,10,15,8))
        self.assertIsNone(result['largest_gap_seconds'])
        self.assertEqual(result['phase'], 'before')
    def test_overnight_ongoing_belongs_to_switch_on_day(self):
        result = observation_summary(self.group([{'at': '2026-10-16T01:00:00', 'lux': 1}]), '22:00', '02:00', datetime(2026,10,16,1,30))
        self.assertEqual(result['phase'], 'ongoing')

if __name__ == '__main__':
    unittest.main()
