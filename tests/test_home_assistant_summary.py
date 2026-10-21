import sys,unittest,tkinter as tk
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_summary import summarize,load_summary,card,health_lines
from ui_palette import THEME_CLAIR,THEME_SOMBRE
from i18n import utiliser_langue

class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.mapping={'hardware_id':'zigbee:0011223344556677','metric':'temperature','model':'ZS-304Z','plant_id':1,'test_data':True}
        self.row={'hardware_id':self.mapping['hardware_id'],'metric':'temperature','ha_updated_at':'2026-10-19T07:00:00+00:00','value':'21','unit':'°C','status':'available','timing_kind':'ha_value_change','gruterra_retrieved_at':'2026-10-19T08:00:00+00:00'}
    def summary(self,rows):
        return summarize([self.mapping],rows,plant_names={1:'Fictional plant'},now='2026-10-19T08:00:00Z')[0]
    def test_test_sensor_plant_and_age(self):
        group=self.summary([self.row]);self.assertTrue(group['test_data']);self.assertEqual(group['plant_name'],'Fictional plant')
        self.assertEqual(group['metrics'][0]['age_minutes'],60)
        self.assertEqual(group['metrics'][0]['status'],'recent')
    def test_latest_contradictory_burst_is_not_a_reliable_single_value(self):
        later={**self.row,'ha_updated_at':'2026-10-19T07:00:00.060000+00:00','value':'22'}
        item=self.summary([self.row,later])['metrics'][0]
        self.assertEqual(item['status'],'burst_conflict')
        self.assertEqual(item['value'],'21–22')

    def test_attribute_update_not_rejuvenating(self):
        row={**self.row,'ha_updated_at':'2026-10-19T07:59:00+00:00','ha_value_changed_at':'2026-10-19T03:00:00+00:00','timing_kind':'ha_attribute_update'}
        item=self.summary([row])['metrics'][0]
        self.assertEqual(item['status'],'stale');self.assertEqual(item['age_minutes'],300)
    def test_initial_state_does_not_hide_previous_real_state(self):
        initial={**self.row,'ha_updated_at':'2026-10-19T07:59:00+00:00','value':'99','timing_kind':'initial_state_uncertain'}
        self.assertEqual(self.summary([self.row,initial])['metrics'][0]['value'],'21')
    def test_missing_and_conflicting_not_zero(self):
        item=self.summary([])['metrics'][0];self.assertIsNone(item['value']);self.assertEqual(item['status'],'missing')
        item=self.summary([{**self.row,'value':None,'status':'conflict'}])['metrics'][0];self.assertIsNone(item['value']);self.assertEqual(item['status'],'conflict')
    def test_devices_never_merged_by_plant(self):
        other={**self.mapping,'hardware_id':'zigbee:0011223344556688'}
        self.assertEqual(len(summarize([self.mapping,other],[self.row])),2)
    def test_demo_no_private_or_network(self):
        with patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch('botaneo_config.lire_json',side_effect=AssertionError('private')),patch('requests.Session',side_effect=AssertionError('network')):
            self.assertTrue(load_summary()['demo'])
    def test_home_card_and_health_french_english_both_themes(self):
        root=tk.Tk();root.geometry('560x720')
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with utiliser_langue(lang),patch('home_assistant_summary.load_summary',return_value={'ok':True,'devices':[self.summary([self.row])]}):
                        frame=card(root,palette);root.update()
                        text=' '.join(w.cget('text') for w in frame.winfo_children() if isinstance(w,tk.Label))
                        self.assertIn('6677',text);self.assertIn('21',text)
                        self.assertTrue(any('6677' in line for line in health_lines()))
                        self.assertEqual(frame.cget('bg'),palette['CARD'])
                        frame.destroy();root.update()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
