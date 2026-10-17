from datetime import datetime
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from light_window_ui import graph_layout

class LightingLayoutTests(unittest.TestCase):
    def group(self, points):
        return {'day': '2026-10-15', 'maximum': max(p['lux'] for p in points), 'points': points}
    def test_full_window_axis_does_not_stretch_sparse_data(self):
        group = self.group([{'at': '2026-10-15T12:00:00', 'lux': 500}])
        layout = graph_layout(group, '09:00', '15:00', 600, 235)
        self.assertAlmostEqual(layout['points'][0]['x'], (layout['left']+layout['right'])/2)
        self.assertEqual(layout['begin'], datetime(2026, 10, 15, 9))
    def test_resize_stays_within_canvas(self):
        group = self.group([{'at': '2026-10-15T09:00:00', 'lux': 0}, {'at': '2026-10-15T14:59:00', 'lux': 700}])
        for width in (320, 550, 1200):
            layout = graph_layout(group, '09:00', '15:00', width, 235)
            for row in layout['points']:
                self.assertLessEqual(row['x'], width)
                self.assertGreaterEqual(row['x'], 0)
                self.assertGreaterEqual(row['y'], 0)
    def test_zero_light_remains_zero_not_missing(self):
        layout = graph_layout(self.group([{'at': '2026-10-15T10:00:00', 'lux': 0}]), '09:00', '15:00', 600, 235)
        self.assertEqual(layout['points'][0]['y'], layout['bottom'])
    def test_overnight_window_and_end_exclusion(self):
        group = self.group([{'at': '2026-10-15T23:00:00', 'lux': 1}, {'at': '2026-10-16T01:00:00', 'lux': 2}, {'at': '2026-10-16T02:00:00', 'lux': 3}])
        layout = graph_layout(group, '22:00', '02:00', 600, 235)
        self.assertEqual(len(layout['points']), 2)
        self.assertEqual(layout['end'], datetime(2026, 10, 16, 2))

if __name__ == '__main__':
    unittest.main()
