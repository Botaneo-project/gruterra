import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'raspberry'))
import weather_sync as sync
import weather_outbox as outbox

class SyncTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.pi=Path(self.tmp.name)/'pi.sqlite3';self.pc=Path(self.tmp.name)/'pc.sqlite3'
  self.config={'enabled':True,'weather_import_enabled':True,'device_id':'pi-fictif'}
  self.row=json.loads((Path(__file__).resolve().parents[1]/'EXEMPLE_METEO_LOT_V1.json').read_text(encoding='utf-8'))['rows'][0]
 def sender(self,config,operation,request=None):
  if operation=='weather_export':return outbox.export_batch(self.pi,config['device_id'])
  return outbox.acknowledge(self.pi,config['device_id'],request)
 def test_real_outbox_to_import_and_empty(self):
  outbox.enqueue(self.pi,'pi-fictif',[self.row])
  first=sync.synchronize(self.config,self.sender,self.pc);self.assertTrue(first['ok']);self.assertEqual(first['added'],1)
  self.assertEqual(outbox.export_batch(self.pi,'pi-fictif')['pending'],0)
  second=sync.synchronize(self.config,self.sender,self.pc);self.assertEqual(second['status'],'empty')
 def test_ack_lost_replay(self):
  outbox.enqueue(self.pi,'pi-fictif',[self.row])
  def lost(config,op,request=None):
   if op=='weather_ack':raise ConnectionError('secret must never appear')
   return self.sender(config,op,request)
  failed=sync.synchronize(self.config,lost,self.pc);self.assertFalse(failed['ok']);self.assertEqual(failed['stage'],'ack');self.assertNotIn('secret',str(failed))
  resumed=sync.synchronize(self.config,self.sender,self.pc);self.assertTrue(resumed['ok']);self.assertEqual(resumed['duplicates'],1)
 def test_ack_delivered_response_lost(self):
  outbox.enqueue(self.pi,'pi-fictif',[self.row])
  def lost(config,op,request=None):
   result=self.sender(config,op,request)
   if op=='weather_ack':raise ConnectionError('lost')
   return result
  self.assertFalse(sync.synchronize(self.config,lost,self.pc)['ok'])
  self.assertEqual(sync.synchronize(self.config,self.sender,self.pc)['status'],'empty')
  self.assertTrue(self.pc.exists())
 def test_disabled_and_empty_do_not_create_pc_database(self):
  def forbidden(*args):raise AssertionError('network forbidden')
  self.assertEqual(sync.synchronize({**self.config,'weather_import_enabled':False},forbidden,self.pc)['status'],'disabled')
  self.assertEqual(sync.synchronize(self.config,self.sender,self.pc)['status'],'empty')
  self.assertFalse(self.pc.exists())

if __name__=='__main__':unittest.main()
