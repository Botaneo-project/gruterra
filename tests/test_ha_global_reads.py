from pathlib import Path
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from test_ha_archive_indexes import build_legacy
from home_assistant_archive import create_read_indexes
from home_assistant_view import read_rows

def build_many(directory,devices=12,states=100):
    plants,archive,cfg,batch=build_legacy(directory,states)
    cfg['entities'][0]['plant_id']=0
    with closing(sqlite3.connect(archive)) as db,db:
        facts=db.execute('SELECT * FROM ha_facts_v1').fetchall()
        versions=db.execute('SELECT * FROM ha_fact_versions_v1').fetchall()
        envelopes=db.execute('SELECT * FROM ha_envelopes_v1').fetchall()
        for index in range(1,devices):
            physical=f'zigbee:{index:016x}'
            entity=f'sensor.fictional_{index}'
            cfg['entities'].append({**cfg['entities'][0],'hardware_id':physical,'entity_id':entity,'plant_id':index%2})
            db.executemany('INSERT INTO ha_facts_v1 VALUES(?,?,?,?)',[(f'{fact}:{index}',physical,metric,stamp) for fact,_,metric,stamp in facts])
            db.executemany('INSERT INTO ha_fact_versions_v1 VALUES(?,?,?)',[(f'{fact}:{index}',revision,content) for fact,revision,content in versions])
            copied=[]
            for _,observation,fact,revision,raw in envelopes:
                record=json.loads(raw);record['hardware_id']=physical;record['entity_id']=entity
                record['raw_state']['entity_id']=entity
                copied.append((physical,f'{observation}:{index}',f'{fact}:{index}',revision,json.dumps(record)))
            db.executemany('INSERT INTO ha_envelopes_v1 VALUES(?,?,?,?,?)',copied)
        create_read_indexes(db)
    return plants,archive,cfg

class GlobalReadTests(unittest.TestCase):
    def test_global_limit_decodes_only_displayed_rows_and_keeps_tie_order(self):
        with tempfile.TemporaryDirectory() as directory:
            plants,archive,cfg=build_many(directory)
            before=archive.read_bytes()
            with patch('home_assistant_view.json.loads',wraps=json.loads) as decode:
                rows=read_rows(archive,cfg['entities'],plant_db_path=plants,limit=40)
                self.assertEqual(decode.call_count,40)
            with closing(sqlite3.connect(archive)) as db:
                expected=db.execute('SELECT fact_id FROM ha_facts_v1 ORDER BY ha_time DESC,physical_id DESC,metric DESC LIMIT 40').fetchall()
            self.assertEqual([row['fact_id'] for row in rows],[row[0] for row in expected])
            self.assertEqual(archive.read_bytes(),before)
            self.assertEqual(rows[0]['status'],'conflict')
    def test_global_limit_still_respects_plant_and_time_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            plants,archive,cfg=build_many(directory)
            rows=read_rows(archive,cfg['entities'],plant_db_path=plants,plant_id=1,
                           start='2026-10-20T03:00:10+02:00',end='2026-10-20T03:00:20+02:00',limit=12)
            allowed={mapping['hardware_id'] for mapping in cfg['entities'] if mapping['plant_id']==1}
            self.assertEqual(len(rows),12)
            self.assertTrue(all(row['hardware_id'] in allowed for row in rows))
            self.assertTrue(all('2026-10-20T01:00:10'<=row['ha_updated_at']<'2026-10-20T01:00:20' for row in rows))

if __name__=='__main__':unittest.main()
