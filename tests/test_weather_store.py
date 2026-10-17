import sys,json,copy,tempfile,sqlite3,unittest
from contextlib import closing
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import weather_protocol as w
from weather_store import import_batch,analysis_candidates

class StoreTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/'weather.sqlite3'
  self.batch=json.loads((Path(__file__).resolve().parents[1]/'EXEMPLE_METEO_LOT_V1.json').read_text(encoding='utf-8'))
 def sign(self,row):
  obs=row['observation'];row['observation_id']='w1_'+w.checksum({k:obs[k] for k in w.IDENTITY_KEYS});row['revision_hash']=w.checksum(obs);return row
 def enriched(self):
  old=self.batch['rows'][0];new=copy.deepcopy(old)
  new['observation']['period'].update(start='2026-10-11T08:00:00Z',end='2026-10-11T09:00:00Z')
  new['observation']['supersedes']={'observation_id':old['observation_id'],'revision_hash':old['revision_hash']}
  return self.sign(new)
 def test_replay_ack_lost_and_legacy_preserved(self):
  with closing(sqlite3.connect(self.path)) as db,db:db.execute('CREATE TABLE pluie (mm REAL)');db.execute('INSERT INTO pluie VALUES (4)')
  counts,ack=import_batch(self.path,self.batch,'pi-fictif');self.assertEqual(counts['added'],1);w.validate_ack(ack,'pi-fictif')
  counts,second=import_batch(self.path,self.batch,'pi-fictif');self.assertEqual(counts['duplicates'],1);self.assertEqual(ack,second)
  with closing(sqlite3.connect(self.path)) as db:self.assertEqual(db.execute('SELECT mm FROM pluie').fetchone()[0],4)
 def test_invalid_lot_has_no_partial_import(self):
  invalid=copy.deepcopy(self.batch);bad=copy.deepcopy(invalid['rows'][0]);bad['observation']['value']='9';invalid['rows'].append(bad);invalid['pending']=2
  with self.assertRaises(ValueError):import_batch(self.path,invalid,'pi-fictif')
  self.assertFalse(self.path.exists())
 def test_revision_preserved_without_guessing(self):
  import_batch(self.path,self.batch,'pi-fictif')
  revised=copy.deepcopy(self.batch);revised['rows'][0]['observation']['value']='3';self.sign(revised['rows'][0])
  counts,_=import_batch(self.path,revised,'pi-fictif');self.assertEqual(counts['revisions'],1);self.assertEqual(analysis_candidates(self.path),[])
  with closing(sqlite3.connect(self.path)) as db:self.assertEqual(db.execute('SELECT count(*) FROM weather_observations_v1').fetchone()[0],2)
 def test_enrichment_resolves_when_predecessor_arrives(self):
  new=self.enriched();import_batch(self.path,{**self.batch,'rows':[new]},'pi-fictif')
  self.assertEqual(analysis_candidates(self.path),[])
  import_batch(self.path,self.batch,'pi-fictif');active=analysis_candidates(self.path)
  self.assertEqual(len(active),1);self.assertEqual(active[0]['observation_id'],new['observation_id'])
 def test_changed_value_cannot_supersede(self):
  import_batch(self.path,self.batch,'pi-fictif');new=self.enriched();new['observation']['value']='8';self.sign(new)
  import_batch(self.path,{**self.batch,'rows':[new]},'pi-fictif')
  active=analysis_candidates(self.path);self.assertEqual(len(active),1);self.assertEqual(active[0]['observation_id'],self.batch['rows'][0]['observation_id'])
 def test_database_failure_rolls_back_whole_batch(self):
  import_batch(self.path,{**self.batch,'rows':[],'pending':0},'pi-fictif')
  with closing(sqlite3.connect(self.path)) as db,db:
   db.execute("CREATE TRIGGER stop_second BEFORE INSERT ON weather_observations_v1 WHEN (SELECT count(*) FROM weather_observations_v1)>0 BEGIN SELECT RAISE(ABORT,'simulated'); END")
  second=copy.deepcopy(self.batch['rows'][0]);second['observation']['source_time']='2026-10-11T10:00:00Z';self.sign(second)
  with self.assertRaises(sqlite3.IntegrityError):import_batch(self.path,{**self.batch,'rows':[self.batch['rows'][0],second],'pending':2},'pi-fictif')
  with closing(sqlite3.connect(self.path)) as db:
   self.assertEqual(db.execute('SELECT count(*) FROM weather_observations_v1').fetchone()[0],0)
   self.assertEqual(db.execute('SELECT count(*) FROM weather_receipts_v1').fetchone()[0],0)

if __name__=='__main__':unittest.main()
