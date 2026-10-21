from pathlib import Path
import sys, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_sensors import prepare

class ZigbeeProfileTests(unittest.TestCase):
    def setUp(self):
        self.mapping = dict(entity_id='sensor.fictional_soil', device_id='fictional', model='ZS-304Z', metric='soil_moisture', hardware_id='zigbee:0011223344556677', test_data=True)
        self.state = dict(entity_id='sensor.fictional_soil', state='2', last_updated='2026-10-18T20:25:32Z', attributes={'unit_of_measurement':'%'})
        self.args = dict(instance_id='fictional', received_at='2026-10-18T20:26:00Z')
    def test_identity_test_marker_and_original_values_preserved(self):
        record=prepare(self.state,self.mapping,**self.args)
        self.assertEqual(record['hardware_id'],self.mapping['hardware_id'])
        self.assertTrue(record['test_data'])
        self.assertEqual(record['value'],'2')
        self.assertIsNone(record['measured_at'])
        self.assertFalse(record['eligible_for_plant_history'])
    def test_repeated_poll_not_new_observation(self):
        a=prepare(self.state,self.mapping,**self.args)
        b=prepare(self.state,self.mapping,instance_id='fictional',received_at='2026-10-18T21:26:00Z')
        self.assertEqual(a['observation_id'],b['observation_id'])
    def test_hardware_normalized_and_different_sensor_distinct(self):
        a=prepare(self.state,self.mapping,**self.args)
        b=prepare(self.state,{**self.mapping,'hardware_id':'zigbee:0x0011223344556677'},**self.args)
        c=prepare(self.state,{**self.mapping,'hardware_id':'zigbee:0011223344556688'},**self.args)
        self.assertEqual(a['observation_id'],b['observation_id'])
        self.assertNotEqual(a['observation_id'],c['observation_id'])
    def test_zigbee_cannot_claim_ble_or_light_sensor_soil(self):
        for change in ({'hardware_id':'ble:001122334455'},{'model':'ZG-106Z'},{'test_data':'false'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                prepare(self.state,{**self.mapping,**change},**self.args)
    def test_arteco_all_four_quantities_and_unknown_not_zero(self):
        for metric,unit in [('soil_moisture','%'),('air_humidity','%'),('temperature','°C'),('illuminance','lx')]:
            record=prepare({**self.state,'state':'unknown','attributes':{'unit_of_measurement':unit}},{**self.mapping,'metric':metric},**self.args)
            self.assertIsNone(record['value'])
    def test_light_sensor_zero_valid(self):
        record=prepare({**self.state,'state':'0','attributes':{'unit_of_measurement':'lx'}},{**self.mapping,'model':'ZG-106Z','metric':'illuminance'},**self.args)
        self.assertEqual(record['value'],'0')

if __name__=='__main__':unittest.main()
