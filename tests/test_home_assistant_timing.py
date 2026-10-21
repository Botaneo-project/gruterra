import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_timing import timing
from home_assistant_sensors import prepare

class TimingTests(unittest.TestCase):
    def record(self,updated,changed=None,reported=None):
        raw={'entity_id':'sensor.fictional','state':'21','last_updated':updated,'attributes':{'unit_of_measurement':'°C'}}
        if changed:raw['last_changed']=changed
        if reported:raw['last_reported']=reported
        return prepare(raw,{'entity_id':'sensor.fictional','device_id':'fictional','model':'ZS-304Z','metric':'temperature'},instance_id='fictional',received_at='2026-10-19T08:00:00Z')
    def test_cached_state_not_rejuvenated_by_retrieval_or_report(self):
        record=self.record('2026-10-19T06:00:00Z','2026-10-19T06:00:00Z','2026-10-19T07:59:00Z')
        result=timing(record)
        self.assertEqual(result['ha_state_updated_at'],'2026-10-19T06:00:00+00:00')
        self.assertEqual(result['gruterra_retrieved_at'],'2026-10-19T08:00:00+00:00')
        self.assertIsNone(result['measured_at']);self.assertFalse(result['physical_acquisition_confirmed'])
    def test_attribute_update_not_new_value(self):
        result=timing(self.record('2026-10-19T07:00:00Z','2026-10-19T06:00:00Z'))
        self.assertEqual(result['timing_kind'],'ha_attribute_update')
    def test_initial_state_never_a_new_timeline_point(self):
        result=timing(self.record('2026-10-19T07:00:00Z'),initial_state=True)
        self.assertFalse(result['usable_for_timeline'])
        self.assertEqual(result['timing_kind'],'initial_state_uncertain')
    def test_optional_bad_date_ignored_without_creating_acquisition(self):
        result=timing(self.record('2026-10-19T07:00:00Z',reported='invalid'))
        self.assertIsNone(result['ha_state_reported_at']);self.assertIsNone(result['measured_at'])
    def test_future_state_excluded(self):
        self.assertFalse(timing(self.record('2026-10-20T07:00:00Z'))['usable_for_timeline'])
    def test_each_quantity_keeps_its_own_time(self):
        a=timing(self.record('2026-10-19T07:00:00Z'))
        b=timing(self.record('2026-10-19T05:00:00Z'))
        self.assertNotEqual(a['ha_state_updated_at'],b['ha_state_updated_at'])
        self.assertEqual(a['gruterra_retrieved_at'],b['gruterra_retrieved_at'])

if __name__=='__main__':unittest.main()
