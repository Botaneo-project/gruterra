import unittest,tempfile,sys
from pathlib import Path
sys.path.insert(0,'C:/Plantes/_app')
from light_schedule import save,load,analyse_profile,profile
class DatedTests(unittest.TestCase):
 def test_history_preserves_previous_days_and_other_metrics(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json';save(p,1,'09:50','15:50')
   value=save(p,1,'10:00','16:00',_day='2026-10-17')
   points=[{'at':'2026-10-16T09:55:00','lux':0,'temperature':22},{'at':'2026-10-17T09:55:00','lux':999},{'at':'2026-10-17T10:00:00','lux':100}]
   groups=analyse_profile(points,value)
   self.assertEqual([g['mean'] for g in groups],[100,0]);self.assertEqual(groups[1]['points'][0]['temperature'],22)
   self.assertEqual(groups[1]['start'],'09:50')
 def test_same_day_replaces_and_noop_preserves(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json';save(p,1,'09:00','15:00')
   save(p,1,'10:00','16:00',_day='2026-10-17')
   value=save(p,1,'11:00','17:00',_day='2026-10-17')
   self.assertEqual(len(value['history']),2)
   self.assertEqual(save(p,1,'11:00','17:00',_day='2026-10-18'),value)
   q=Path(d)/'q.json';save(q,2,value['start'],value['end'],_profile=value)
   self.assertEqual(load(q,2),value)
 def test_overnight_uses_lighting_day(self):
  value={'start':'23:00','end':'03:00','history':[{'from':'0001-01-01','start':'22:00','end':'02:00'},{'from':'2026-10-17','start':'23:00','end':'03:00'}]}
  groups=analyse_profile([{'at':'2026-10-17T01:00:00','lux':0},{'at':'2026-10-17T22:30:00','lux':999},{'at':'2026-10-18T02:30:00','lux':10}],value)
  self.assertEqual([(g['day'],g['mean']) for g in groups],[('2026-10-17',10),('2026-10-16',0)])
 def test_invalid_history_rejected(self):
  with self.assertRaises(ValueError):profile({'start':'10:00','end':'16:00','history':[{'from':'2026-10-17','start':'09:00','end':'15:00'}]})
 def test_clock_rollback_preserves_file(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'s.json';save(p,1,'09:00','15:00');save(p,1,'10:00','16:00',_day='2026-10-17');before=p.read_bytes()
   with self.assertRaises(ValueError):save(p,1,'11:00','17:00',_day='2026-10-16')
   self.assertEqual(p.read_bytes(),before)
if __name__=='__main__':unittest.main()
