import copy,json,sys,unittest
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import weather_protocol as w

class ProtocolTests(unittest.TestCase):
 def setUp(self):
  self.batch=json.loads((Path(__file__).resolve().parents[1]/'EXEMPLE_METEO_LOT_V1.json').read_text(encoding='utf-8'))
  self.row=self.batch['rows'][0]
 def sign(self,row):
  obs=row['observation']
  row['observation_id']='w1_'+w.checksum({k:obs[k] for k in w.IDENTITY_KEYS})
  row['revision_hash']=w.checksum(obs)
  return row
 def test_vectors_and_replay(self):
  w.validate_batch(self.batch,'pi-fictif')
  w.validate_batch(w.decode(w.canonical(self.batch)),'pi-fictif')
  replay=copy.deepcopy(self.row);replay['retrieved_at']='2026-10-11T10:00:00Z'
  w.validate_row(replay)
  self.assertEqual(replay['revision_hash'],self.row['revision_hash'])
 def test_revision_and_ack_lost(self):
  revised=copy.deepcopy(self.row);revised['observation']['value']='3';revised=self.sign(revised)
  self.assertEqual(revised['observation_id'],self.row['observation_id'])
  self.assertNotEqual(revised['revision_hash'],self.row['revision_hash'])
  ack={'protocol':w.PROTOCOL,'protocol_version':1,'device_id':'pi-fictif','rows':[{'observation_id':self.row['observation_id'],'revision_hash':self.row['revision_hash']}]}
  for _ in range(2):w.validate_ack(ack,'pi-fictif')
  ack['rows']*=2
  with self.assertRaises(ValueError):w.validate_ack(ack,'pi-fictif')
 def test_module_unknown_priority(self):
  row=copy.deepcopy(self.row);row['observation']['module_id']=None;self.sign(row)
  with self.assertRaises(ValueError):w.validate_row(row)
  row['observation_id']='wu1_'+str(uuid4());w.validate_row(row)
 def test_period_enrichment_link(self):
  row=copy.deepcopy(self.row)
  row['observation']['period'].update(start='2026-10-11T08:00:00Z',end='2026-10-11T09:00:00Z')
  row['observation']['supersedes']={'observation_id':self.row['observation_id'],'revision_hash':self.row['revision_hash']}
  self.sign(row);w.validate_row(row)
  self.assertNotEqual(row['observation_id'],self.row['observation_id'])
 def test_zero_null_missing_and_invalid_decimal(self):
  for value in ('0',None):
   row=copy.deepcopy(self.row);row['observation']['value']=value;w.validate_row(self.sign(row))
  for value in ('-0','2.40','NaN',2.4,'-1'):
   row=copy.deepcopy(self.row);row['observation']['value']=value
   with self.assertRaises(ValueError):w.validate_row(self.sign(row))
  row=copy.deepcopy(self.row);del row['observation']['value']
  with self.assertRaises(ValueError):w.validate_row(row)
 def test_bytes_bound_and_nonempty(self):
  second=copy.deepcopy(self.row);second['observation']['source_time']='2026-10-11T10:00:00Z';self.sign(second)
  limit=len(w.canonical({**self.batch,'pending':2}))
  batch=w.pack_batch([self.row,second],2,'pi-fictif',limit)
  self.assertEqual(len(batch['rows']),1)
  with self.assertRaises(ValueError):w.pack_batch([self.row],1,'pi-fictif',100)
  with self.assertRaises(ValueError):w.validate_batch({**self.batch,'rows':[]},'pi-fictif')
 def test_strict_json_identity_and_tampering(self):
  for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'\xef\xbb\xbf{}'):
   with self.assertRaises(ValueError):w.decode(raw)
  with self.assertRaises(ValueError):w.validate_batch(self.batch,'other-pi')
  self.row['observation']['value']='6'
  with self.assertRaises(ValueError):w.validate_row(self.row)

if __name__=='__main__':unittest.main()
