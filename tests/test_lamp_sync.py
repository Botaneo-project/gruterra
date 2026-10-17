import importlib.util,sys,tempfile,unittest,json,types,sqlite3
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import light_schedule as light
import lamp_sync as sync
A={'start':'09:50','end':'15:50'};B={'start':'09:15','end':'15:15'};C={'start':'10:00','end':'16:00'}
class Tests(unittest.TestCase):
 def test_decisions(self):
    for base,pc,pi,known,expected in [(None,A,A,False,'equal'),(None,A,B,False,'conflict'),(A,B,A,True,'push'),(A,A,B,True,'pull'),(A,B,C,True,'conflict'),(None,None,A,False,'pull'),(None,A,None,False,'push')]:self.assertEqual(sync.decision(base,pc,pi,known),expected)
 def test_roundtrip_conflict_and_resolution(self):
    with tempfile.TemporaryDirectory() as d:
     root=Path(d);db=root/'test.db'
     with sqlite3.connect(db) as conn:
      conn.execute('CREATE TABLE capteurs(plante_id,adresse_ble,actif)');conn.execute("INSERT INTO capteurs VALUES(1,'AA',1)")
     conn.close()
     remote=[A.copy()]
     def sender(config,op,req):
      if op=='lamp_set':
       ok=remote[0]==req['expected']
       if ok:remote[0]=req['value']
       return {'device_id':'test','ok':ok,'value':remote[0]}
      return {'device_id':'test','schedule_version':2,'value':remote[0]}
     modules={'database':types.SimpleNamespace(get_connection=lambda:sqlite3.connect(db)),'raspberry_sync':types.SimpleNamespace(transport=sender)}
     config={'enabled':True,'sensors':['AA'],'device_id':'test'}
     with patch.dict(sys.modules,modules),patch.object(sync,'ROOT',root):
      light.save(root/'light-schedules.json',1,**dict(start=A['start'],end=A['end']))
      sync.synchronize(config,sender)
      saved_b=light.save(root/'light-schedules.json',1,B['start'],B['end']);sync.synchronize(config,sender);self.assertEqual(remote[0],saved_b)
      remote[0]=C.copy();sync.synchronize(config,sender);self.assertEqual(light.load(root/'light-schedules.json',1),C)
      saved_a=light.save(root/'light-schedules.json',1,A['start'],A['end']);remote[0]=B.copy()
      self.assertIn('conflit',sync.synchronize(config,sender));self.assertEqual(light.load(root/'light-schedules.json',1),saved_a);self.assertEqual(remote[0],B)
      sync.synchronize(config,sender,{'plant':'1','pc':saved_a,'pi':B,'choice':'pi'});self.assertEqual(light.load(root/'light-schedules.json',1),B)
      # A lost response after the Pi commits must converge on retry.
      saved_c=light.save(root/'light-schedules.json',1,C['start'],C['end'])
      def lost(config,op,req):
       result=sender(config,op,req)
       if op=='lamp_set':raise ConnectionError('lost response')
       return result
      with self.assertRaises(ConnectionError):sync.synchronize(config,lost)
      self.assertEqual(remote[0],saved_c)
      sync.synchronize(config,sender)
      self.assertEqual(json.loads((root/'light-sync-state.json').read_text())['test|AA']['base'],saved_c)
      # A concurrent Pi change must reject the PC write.
      saved_a=light.save(root/'light-schedules.json',1,A['start'],A['end'])
      def raced(config,op,req):
       if op=='lamp_set':remote[0]=B.copy()
       return sender(config,op,req)
      self.assertIn('conflit',sync.synchronize(config,raced))
      self.assertEqual(remote[0],B);self.assertEqual(light.load(root/'light-schedules.json',1),saved_a)
      # A conflict choice based on obsolete values must not overwrite anything.
      with self.assertRaises(ValueError):sync.synchronize(config,sender,{'plant':'1','pc':C,'pi':B,'choice':'pc'})
      self.assertEqual(remote[0],B)
      # A wholly unavailable Pi leaves local settings and baseline unchanged.
      before=(root/'light-sync-state.json').read_bytes()
      with self.assertRaises(ConnectionError):sync.synchronize(config,lambda *a:(_ for _ in ()).throw(ConnectionError()))
      self.assertEqual((root/'light-sync-state.json').read_bytes(),before)
if __name__=='__main__':unittest.main()
