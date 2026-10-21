from datetime import datetime
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from light_schedule import analyse, date_eclairage
from light_window_ui import graph_layout, observation_summary

class LightingTimezoneTests(unittest.TestCase):
    def test_utc_readings_near_midnight_match_analysis_and_plot(self):
        points=[{'at':'2026-10-17T22:30:00Z','lux':100},
                {'at':'2026-10-18T00:45:00+02:00','lux':200}]
        groups=analyse(points,'00:00','02:00')
        self.assertEqual(groups[0]['day'],'2026-10-18')
        layout=graph_layout(groups[0],'00:00','02:00',600,235)
        self.assertEqual(groups[0]['count'],len(layout['points']))
        self.assertEqual([p['at'] for p in layout['points']], [datetime(2026,10,18,0,30),datetime(2026,10,18,0,45)])
    def test_winter_clock_and_summary_use_same_zone(self):
        points=[{'at':'2026-12-10T08:30:00Z','lux':0}]
        group=analyse(points,'09:00','10:00')[0]
        result=observation_summary(group,'09:00','10:00','2026-12-10T08:45:00Z')
        self.assertEqual(result['phase'],'ongoing')
        self.assertEqual(result['first'],datetime(2026,12,10,9,30))
        self.assertEqual(date_eclairage('2026-10-25T02:30:00+01:00'),datetime(2026,10,25,2,30))
