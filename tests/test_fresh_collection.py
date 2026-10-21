import ast,asyncio,logging,json,sys,unittest,tempfile
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import raspberry_sync as sync


class CollectionOrderTests(unittest.TestCase):
    def cycle(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/'raspberry/collector/collector.py').read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='cycle')
        env={'asyncio':asyncio,'logging':logging,'record':Mock()}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'collector-cycle','exec'),env)
        return env
    def test_all_current_readings_stored_before_any_history(self):
        env=self.cycle();events=[]
        async def read(sensor,**kw):events.append('current-'+sensor);return (22,16,100,20,'fake')
        async def history(path,device,sensor):events.append('history-'+sensor);return 'ok',0
        asyncio.run(env['cycle']({'sensors':['a','b'],'device_id':'fake'},None,read,history))
        self.assertEqual(events,['current-a','current-b','history-a','history-b'])
        self.assertEqual(env['record'].call_count,2)
    def test_priority_request_interrupts_history_and_closes_it(self):
        env=self.cycle();closed=[]
        with tempfile.TemporaryDirectory() as folder:
            request=Path(folder)/'request'
            async def read(sensor,**kw):return (22,16,100,20,'fake')
            async def history(*args):
                request.touch()
                try:await asyncio.sleep(10)
                finally:closed.append(True)
            asyncio.run(env['cycle']({'sensors':['a'],'device_id':'fake'},None,read,history,request_path=request))
        self.assertEqual(closed,[True]);env['record'].assert_called_once()


class FreshImportTests(unittest.TestCase):
    def run_sync(self,batches,status='pending',ticks=None):
        def sender(config,operation,request=None):
            if operation=='collect_now':return {'accepted':False,'status':status,'message':'fictional'}
            if operation=='export':return batches.pop(0)
            raise AssertionError(operation)
        def imported(path,batch,config):
            counts={key:0 for key in ('added','duplicates','undated','history_added','history_duplicates','history_undated','current_added','current_duplicates','current_undated')}
            counts['added']=counts['current_added']=len(batch['rows'])
            return counts,{'rows':[]}
        with patch.object(sync,'import_batch',side_effect=imported),patch.object(sync.time,'sleep'),patch.object(sync.time,'monotonic',side_effect=ticks or [0,0]):
            return sync.synchronize({'sensors':['A'],'away':False,'enabled':True},sender,'fake.db',True)
    def test_running_collection_is_polled_until_fresh_reading_arrives(self):
        row={'kind':'current','time_quality':'ntp','sensor_id':'A','measured_at':datetime.now(timezone.utc).isoformat()}
        result=self.run_sync([{'pending':0,'rows':[]},{'pending':1,'rows':[row]}],status='running')
        self.assertTrue(result['ok']);self.assertTrue(result['fresh_measurement_confirmed'])
    def test_old_current_does_not_count_as_new_measurement(self):
        row={'kind':'current','time_quality':'ntp','sensor_id':'A','measured_at':'2020-01-01T00:00:00+00:00'}
        result=self.run_sync([{'pending':1,'rows':[row]},{'pending':0,'rows':[]}],ticks=[0,0,121])
        self.assertFalse(result['ok']);self.assertTrue(result['collection_pending'])
        self.assertEqual(result['current_added'],1)
