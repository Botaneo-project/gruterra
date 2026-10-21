from pathlib import Path
from datetime import datetime,timedelta,timezone
from contextlib import closing
import json
import sqlite3
import tempfile
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_archive import commit_history,create_read_indexes
from home_assistant_sensors import prepare
from home_assistant_view import read_rows

INDEXES=('ha_facts_by_device_metric_time','ha_envelopes_by_fact_observation','ha_windows_by_start')

def build_legacy(directory,count=3000):
    plants=Path(directory)/'plants.db';archive=Path(directory)/'history.db'
    with closing(sqlite3.connect(plants)) as db,db:db.execute('CREATE TABLE capteurs(adresse_ble TEXT)')
    mapping={'entity_id':'sensor.fictional','device_id':'fictional','model':'fictional','metric':'illuminance',
             'hardware_id':'zigbee:0011223344556677','hardware_confirmed':True,'test_data':True}
    config={'schema_version':1,'enabled':True,'base_url':'https://example.invalid','access_token':'fictional',
            'instance_id':'fictional','entities':[mapping]}
    batch={'ok':True,'http_status':200,'start':'2026-10-20T00:00:00Z','end':'2026-10-20T06:00:00Z','records':[]}
    commit_history(archive,config,batch,plant_db_path=plants)
    facts=[];versions=[];envelopes=[]
    begin=datetime(2026,10,20,1,tzinfo=timezone.utc)
    for index in range(count):
        stamp=(begin+timedelta(seconds=index)).isoformat()
        record=prepare({'entity_id':mapping['entity_id'],'state':str(index%100),'attributes':{'unit_of_measurement':'lx'},
                        'last_changed':stamp,'last_updated':stamp},mapping,instance_id='fictional',received_at='2026-10-20T06:00:00Z')
        fact=f'fictional-{index}'
        facts.append((fact,mapping['hardware_id'],'illuminance',stamp))
        versions.append((fact,'original','{}'))
        envelopes.append((mapping['hardware_id'],record['observation_id'],fact,'original',json.dumps(record)))
    # Fixture-only legacy archive; the application never performs this direct insertion.
    with closing(sqlite3.connect(archive)) as db,db:
        db.executemany('INSERT INTO ha_facts_v1 VALUES(?,?,?,?)',facts)
        db.executemany('INSERT INTO ha_fact_versions_v1 VALUES(?,?,?)',versions)
        db.executemany('INSERT INTO ha_envelopes_v1 VALUES(?,?,?,?,?)',envelopes)
        db.execute("INSERT INTO ha_fact_versions_v1 VALUES(?,?,?)",(facts[-1][0],'conflicting','{}'))
        for index in INDEXES:db.execute('DROP INDEX '+index)
    return plants,archive,config,batch

class ArchiveIndexTests(unittest.TestCase):
    def test_indexed_and_legacy_results_match_including_conflict_without_rewriting_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            plants,archive,cfg,batch=build_legacy(directory)
            before=read_rows(archive,cfg['entities'],plant_db_path=plants,limit=100)
            with closing(sqlite3.connect(archive)) as db:
                originals={table:db.execute('SELECT * FROM '+table).fetchall() for table in ('ha_facts_v1','ha_fact_versions_v1','ha_envelopes_v1','ha_cursor_v1')}
                with db:create_read_indexes(db)
                for table,rows in originals.items():self.assertEqual(db.execute('SELECT * FROM '+table).fetchall(),rows)
                details=' '.join(row[3] for row in db.execute('EXPLAIN QUERY PLAN SELECT fact_id FROM ha_facts_v1 WHERE physical_id=? AND metric=? ORDER BY ha_time DESC LIMIT 100',('fictional','illuminance')))
                self.assertIn(INDEXES[0],details)
                details=' '.join(row[3] for row in db.execute('EXPLAIN QUERY PLAN SELECT record_json FROM ha_envelopes_v1 WHERE fact_id=? ORDER BY observation_id LIMIT 1',('fictional',)))
                self.assertIn(INDEXES[1],details)
            after=read_rows(archive,cfg['entities'],plant_db_path=plants,limit=100)
            self.assertEqual(after,before)
            self.assertEqual(after[0]['status'],'conflict');self.assertIsNone(after[0]['value'])
    def test_next_commit_upgrades_legacy_indexes_without_touching_plant_database(self):
        with tempfile.TemporaryDirectory() as directory:
            plants,archive,cfg,batch=build_legacy(directory,10);before=plants.read_bytes()
            result=commit_history(archive,cfg,batch,plant_db_path=plants)
            self.assertEqual(result['facts_added'],0)
            self.assertEqual(plants.read_bytes(),before)
            with closing(sqlite3.connect(archive)) as db:
                names={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
                self.assertTrue(set(INDEXES)<=names)
    def test_index_creation_rolls_back_with_failed_history_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            plants,archive,cfg,batch=build_legacy(directory,10)
            with closing(sqlite3.connect(archive)) as db,db:
                db.execute("CREATE TRIGGER fail_cursor BEFORE INSERT ON ha_cursor_v1 BEGIN SELECT RAISE(ABORT,'fictional failure'); END")
            with self.assertRaises(sqlite3.DatabaseError):
                commit_history(archive,cfg,{**batch,'start':batch['end'],'end':'2026-10-20T12:00:00Z'},plant_db_path=plants)
            with closing(sqlite3.connect(archive)) as db:
                names={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
                self.assertFalse(set(INDEXES)&names)
                self.assertEqual(db.execute('SELECT end_time FROM ha_cursor_v1').fetchone()[0],'2026-10-20T06:00:00+00:00')

if __name__=='__main__':unittest.main()
