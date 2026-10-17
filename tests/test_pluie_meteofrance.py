import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import pluie_meteofrance as m

class RainTests(unittest.TestCase):
 def setUp(self):self.station={'station':'00000001','name':'Fictive','distance_m':100}
 def test_zero_null_absent_and_date(self):
  data=[{'validity_time':'2026-10-12T16:00:00Z','rr1':0},{'validity_time':'2026-10-12T17:00:00Z','rr1':None},{'validity_time':'2026-10-12T18:00:00Z'},{'validity_time':'bad','rr1':2},{'validity_time':'2026-10-12T19:00:00Z','rr1':-1}]
  rows=m.normalise(data,self.station);self.assertEqual(len(rows),2);self.assertEqual(rows[0]['mm'],0);self.assertIsNone(rows[1]['mm']);self.assertEqual(rows[0]['period_seconds'],3600)
 def test_wrong_station_and_utc(self):
  self.assertEqual(m.normalise([{'geo_id_insee':'other','validity_time':'2026-10-12T16:00:00Z','rr1':2}],self.station),[])
  self.assertEqual(m.utc('2026-10-12T18:00:00+02:00'),'2026-10-12T16:00:00Z')
  with self.assertRaises(ValueError):m.utc('2026-10-12T16:00:00')
 def test_dedup_and_revision_in_separate_database(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'meteofrance_pluie.sqlite3';main=Path(d)/'plantes.db';main.write_bytes(b'untouched')
   rows=m.normalise([{'validity_time':'2026-10-12T16:00:00Z','rr1':2}],self.station)
   self.assertEqual(m.save(path,rows),1);self.assertEqual(m.save(path,rows),0)
   rows[0]['mm']=3;self.assertEqual(m.save(path,rows),1);self.assertEqual(len(m.read(path)),2);self.assertEqual(main.read_bytes(),b'untouched')
 def test_nearest_preserves_leading_zero(self):
  rows=[{'Id_station':'00000001','Nom_usuel':'Near','Latitude':'48,8','Longitude':'2,2'},{'Id_station':'00000002','Nom_usuel':'Far','Latitude':'49','Longitude':'3'}]
  self.assertEqual(m.nearest(rows,48.8,2.2)[0]['station'],'00000001')

if __name__=='__main__':unittest.main()
