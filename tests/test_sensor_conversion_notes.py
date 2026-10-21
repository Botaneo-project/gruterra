import unittest,sys,json,tempfile,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from sensor_conversion_notes import load_notes,relevant_notes
class ConversionNotesTests(unittest.TestCase):
    def test_demo_does_not_read_private_files(self):
        with patch.dict(os.environ,{'BOTANEO_DEMO':'1'}),patch.object(Path,'read_text',side_effect=AssertionError('private')):
            self.assertEqual(load_notes(),[])
    def test_valid_marker_scoped_to_lux_and_hardware(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'marker.json'
            p.write_text(json.dumps({'schema_version':1,'activated_at':'2026-10-19T13:17:27+02:00','hardware_ids':['zigbee:fictional']}),encoding='utf-8')
            notes=load_notes(p)
            rows=[{'metric':'illuminance','hardware_id':'zigbee:fictional'}]
            self.assertEqual(len(relevant_notes(notes,rows)),1)
            self.assertEqual(relevant_notes(notes,rows,'temperature'),[])
            self.assertEqual(relevant_notes(notes,[{'metric':'illuminance','hardware_id':'other'}]),[])
    def test_invalid_or_naive_marker_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'marker.json'
            for data in ('{bad',json.dumps({'schema_version':1,'activated_at':'2026-10-19T13:17:27','hardware_ids':['fictional']})):
                p.write_text(data,encoding='utf-8');self.assertEqual(load_notes(p),[])
if __name__=='__main__':unittest.main()
