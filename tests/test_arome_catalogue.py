import sys,unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import arome_catalogue as m

class AromeTests(unittest.TestCase):
 def test_fixed_schedule_midnight(self):
  now=datetime(2026,10,12,23,59,59,tzinfo=timezone.utc)
  self.assertEqual(m.next_scan(now).isoformat(),'2026-10-13T00:00:01+00:00')
  now=now.replace(hour=20,minute=15,second=0)
  self.assertEqual(m.next_scan(now).minute,15)
  self.assertEqual(m.next_scan(now.replace(second=1)).minute,30)
 def test_naive_time_rejected(self):
  with self.assertRaises(ValueError):m.next_scan(datetime(2026,10,12))
 def test_select_recent_not_first_or_future(self):
  ids=[f'TOTAL_WATER_PRECIPITATION__GROUND_OR_WATER_SURFACE___2026-10-12T{hour:02d}.00.00Z_PT15M' for hour in (8,19,18)]
  raw=('<Capabilities>'+''.join('<CoverageId>'+value+'</CoverageId>' for value in ids)+'</Capabilities>').encode()
  self.assertEqual(m.latest_rain(raw,datetime(2026,10,12,18,30,tzinfo=timezone.utc)),ids[-1])
  with self.assertRaises(ValueError):m.latest_rain(raw,datetime(2026,10,13,1,tzinfo=timezone.utc))
 def test_invalid_xml_and_entities(self):
  for raw in (b'bad',b'<!DOCTYPE test><test/>'):
   with self.assertRaises(ValueError):m.xml(raw)

if __name__=='__main__':unittest.main()
