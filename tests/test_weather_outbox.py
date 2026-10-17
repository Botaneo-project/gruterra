from contextlib import closing
import copy
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'_app'), str(ROOT/'raspberry')]
import weather_protocol as protocol
import weather_outbox as pi
import weather_store as pc


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.path = self.base/'pi.sqlite3'
        self.row = json.loads((ROOT/'EXEMPLE_METEO_LOT_V1.json').read_text(encoding='utf-8'))['rows'][0]
        self.device = 'pi-fictif'

    def batch(self):
        return pi.export_batch(self.path, self.device)

    def test_lost_ack_reopen_and_replay(self):
        pi.enqueue(self.path,self.device,[self.row])
        first=self.batch()
        counts, ack=pc.import_batch(self.base/'pc.sqlite3',first,self.device)
        self.assertEqual(counts['added'],1)
        self.assertEqual(first,self.batch())  # Simulates process restart with lost ACK.
        counts,again=pc.import_batch(self.base/'pc.sqlite3',self.batch(),self.device)
        self.assertEqual(counts['duplicates'],1)
        self.assertEqual(ack,again)
        self.assertEqual(pi.acknowledge(self.path,self.device,ack)['confirmed'],1)
        self.assertEqual(pi.acknowledge(self.path,self.device,ack)['confirmed'],1)
        self.assertEqual(self.batch()['pending'],0)
        self.assertEqual(pi.enqueue(self.path,self.device,[self.row]),0)
        self.assertEqual(self.batch()['pending'],0)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM weather_outbox_v1').fetchone()[0],1)

    def test_ack_failure_is_atomic(self):
        pi.enqueue(self.path,self.device,[self.row])
        pair={k:self.row[k] for k in ('observation_id','revision_hash')}
        ack=dict(protocol=protocol.PROTOCOL,protocol_version=1,device_id=self.device,rows=[pair,{**pair,'revision_hash':'0'*64}])
        with self.assertRaises(ValueError):pi.acknowledge(self.path,self.device,ack)
        self.assertEqual(self.batch()['pending'],1)
        ack['rows']=[pair,pair]
        with self.assertRaises(ValueError):pi.acknowledge(self.path,self.device,ack)

    def test_revisions_are_separate(self):
        new=copy.deepcopy(self.row)
        new['observation']['value']='3'
        new['revision_hash']=protocol.checksum(new['observation'])
        pi.enqueue(self.path,self.device,[self.row,new])
        counts,ack=pc.import_batch(self.base/'pc.sqlite3',self.batch(),self.device)
        self.assertEqual(counts['revisions'],1)
        ack['rows']=ack['rows'][:1]
        pi.acknowledge(self.path,self.device,ack)
        self.assertEqual(self.batch()['rows'],[new])
        self.assertEqual(pc.analysis_candidates(self.base/'pc.sqlite3'),[])

    def test_bounded_export_and_identity(self):
        rows=[]
        for i in range(501):
            row=copy.deepcopy(self.row)
            row['observation']['module_id']='module-'+str(i)
            row['observation_id']='w1_'+protocol.checksum({k:row['observation'][k] for k in protocol.IDENTITY_KEYS})
            row['revision_hash']=protocol.checksum(row['observation'])
            rows.append(row)
        pi.enqueue(self.path,self.device,rows)
        batch=self.batch()
        self.assertEqual(len(batch['rows']),500)
        self.assertEqual(batch['pending'],501)
        limit=len(protocol.canonical({**batch,'rows':rows[:1]}))
        self.assertEqual(len(pi.export_batch(self.path,self.device,limit)['rows']),1)
        with self.assertRaises(ValueError):pi.export_batch(self.path,self.device,100)
        with self.assertRaises(ValueError):pi.export_batch(self.path,'wrong-device')

    def test_empty_export(self):
        self.assertEqual(self.batch()['rows'],[])
        self.assertEqual(self.batch()['pending'],0)

    def test_invalid_enqueue_leaves_no_partial_rows(self):
        bad=copy.deepcopy(self.row);bad['observation']['value']='8'
        with self.assertRaises(ValueError):pi.enqueue(self.path,self.device,[self.row,bad])
        self.assertFalse(self.path.exists())


if __name__=='__main__':unittest.main()
