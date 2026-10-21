import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_chart import chart_data
class ChartValuesTests(unittest.TestCase):
    def row(self,value,**kwargs):
        return {'metric':'soil_moisture','value':value,'hardware_id':'fictional','ha_updated_at':'2026-10-19T08:00:00+00:00','status':'available',**kwargs}
    def test_archived_decimal_strings_and_zero(self):
        model=chart_data([self.row('0'),self.row('9.5')],'soil_moisture')
        self.assertEqual([p[1] for p in model['points']],[0,9.5])
        self.assertLess(model['high'],100)
        full=chart_data([self.row('9.5')],'soil_moisture',full_scale=True)
        self.assertEqual((full['low'],full['high']),(0,100))
    def test_invalid_and_non_measurement_states_are_excluded(self):
        for value in (None,True,'unknown','unavailable','NaN','Infinity',''):
            with self.subTest(value=value):self.assertIsNone(chart_data([self.row(value)],'soil_moisture'))
        for extra in ({'status':'conflict'},{'timing_kind':'initial_state_uncertain'},{'timing_kind':'ha_attribute_update'}):
            self.assertIsNone(chart_data([self.row('9',**extra)],'soil_moisture'))
class BurstTests(unittest.TestCase):
    def test_bounded_groups_keep_all_states_and_devices_separate(self):
        from home_assistant_chart import group_bursts
        points=[(0,11,'a'),(.06,2,'a'),(.5,50,'b'),(.9,3,'a'),(1.1,7,'a')]
        groups=group_bursts(points)
        self.assertEqual(sum(map(len,groups)),len(points))
        self.assertTrue(all(len({p[2] for p in g})==1 for g in groups))
        self.assertTrue(all(g[-1][0]-g[0][0]<1 for g in groups))
        self.assertEqual(len(groups),3)

if __name__=='__main__':unittest.main()
