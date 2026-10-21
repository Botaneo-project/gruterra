import copy
from contextlib import closing
import sqlite3
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import test_home_assistant_archive as archive_tests
from home_assistant_test_data import preview_test_purge, purge_test_data

class TestPurge(archive_tests.ArchiveTests):
    def setUp(self):
        super().setUp()
        self.mapping['test_data']=True
        self.batch['records']=[self.record()]
    def plan(self):
        return preview_test_purge(self.archive,self.mapping['hardware_id'],start=self.batch['start'],end=self.batch['end'],plant_db_path=self.plants)
    def test_backup_purge_replay_and_plant_untouched(self):
        before=self.plants.read_bytes()
        self.commit()
        plan=self.plan()
        self.assertEqual(plan['facts'],1)
        result=purge_test_data(self.archive,plan,confirmed=True,plant_db_path=self.plants)
        with closing(sqlite3.connect(result['backup'])) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM ha_facts_v1').fetchone()[0],1)
        self.assertEqual(self.commit()['excluded'],1)
        with closing(sqlite3.connect(self.archive)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM ha_facts_v1').fetchone()[0],0)
        self.assertEqual(before,self.plants.read_bytes())
    def test_confirmation_required(self):
        self.commit()
        with self.assertRaisesRegex(ValueError,'confirmation_required'):
            purge_test_data(self.archive,self.plan(),plant_db_path=self.plants)
    def test_normal_data_not_selected(self):
        self.mapping['test_data']=False
        self.batch['records']=[self.record()]
        self.commit()
        self.assertEqual(self.plan()['facts'],0)
    def test_changed_plan_rejected(self):
        self.commit()
        plan=self.plan()
        self.commit({**self.batch,'records':[self.record('15')]})
        with self.assertRaisesRegex(ValueError,'plan_changed'):
            purge_test_data(self.archive,plan,confirmed=True,plant_db_path=self.plants)
    def test_other_device_and_outside_period_not_selected(self):
        self.commit()
        other=preview_test_purge(self.archive,'zigbee:0011223344556688',start=self.batch['start'],end=self.batch['end'],plant_db_path=self.plants)
        self.assertEqual(other['facts'],0)
        later=preview_test_purge(self.archive,self.mapping['hardware_id'],start='2026-10-16T00:00:00Z',end='2026-10-17T00:00:00Z',plant_db_path=self.plants)
        self.assertEqual(later['facts'],0)

    def test_backup_failure_leaves_archive_unchanged(self):
        self.commit()
        plan=self.plan()
        blocked=self.archive.with_name(self.archive.name+'.before-test-purge-blocked.sqlite3')
        blocked.mkdir()
        before=self.archive.read_bytes()
        with patch('home_assistant_test_data.uuid.uuid4',return_value=SimpleNamespace(hex='blocked')):
            with self.assertRaises(sqlite3.OperationalError):
                purge_test_data(self.archive,plan,confirmed=True,plant_db_path=self.plants)
        self.assertEqual(before,self.archive.read_bytes())
        self.assertEqual(self.plan()['facts'],1)
    def test_delete_failure_rolls_back_all_tables(self):
        self.commit()
        with closing(sqlite3.connect(self.archive)) as db,db:
            db.execute("CREATE TRIGGER refuse_delete BEFORE DELETE ON ha_envelopes_v1 BEGIN SELECT RAISE(ABORT,'simulated'); END")
        plan=self.plan()
        with self.assertRaises(sqlite3.DatabaseError):
            purge_test_data(self.archive,plan,confirmed=True,plant_db_path=self.plants)
        self.assertEqual(self.plan(),plan)
        with closing(sqlite3.connect(self.archive)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM ha_fact_versions_v1').fetchone()[0],1)
            self.assertFalse(db.execute("SELECT 1 FROM sqlite_master WHERE name='ha_excluded_facts_v1'").fetchone())
        self.assertEqual(len(list(self.archive.parent.glob('*.before-test-purge-*.sqlite3'))),1)
    def test_mixed_test_and_regular_fact_never_selected(self):
        self.commit()
        self.mapping['test_data']=False
        self.commit({**self.batch,'records':[self.record()]})
        self.assertEqual(self.plan()['facts'],0)
    def test_demo_and_plant_database_blocked(self):
        self.commit()
        plan=self.plan()
        with patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),self.assertRaisesRegex(ValueError,'demo_disabled'):
            purge_test_data(self.archive,plan,confirmed=True,plant_db_path=self.plants)
        with self.assertRaisesRegex(ValueError,'plant_database_forbidden'):
            preview_test_purge(self.plants,self.mapping['hardware_id'],start=self.batch['start'],end=self.batch['end'],plant_db_path=self.plants)
    def test_alias_and_revision_still_excluded_after_removal(self):
        self.commit()
        purge_test_data(self.archive,self.plan(),confirmed=True,plant_db_path=self.plants)
        config={**self.config,'entities':[{**self.mapping,'entity_id':'sensor.renamed'}]}
        result=self.commit({**self.batch,'records':[self.record('15','sensor.renamed')]},config)
        self.assertEqual(result['excluded'],1)
        self.assertEqual(result['facts_added'],0)

if __name__=='__main__':unittest.main()
