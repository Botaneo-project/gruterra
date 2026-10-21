from pathlib import Path
import sys,sqlite3,unittest,tkinter as tk
from unittest.mock import patch
from contextlib import closing
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import test_home_assistant_archive as fixtures
from home_assistant_view import read_rows
from home_assistant_sync import synchronize
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

class ViewTests(fixtures.ArchiveTests):
    def test_plant_filter_read_only_and_conflicts(self):
        self.mapping.update(plant_id=7,test_data=True)
        self.batch['records']=[self.record()];self.commit()
        before=self.archive.read_bytes()
        rows=read_rows(self.archive,[self.mapping],plant_id=7,plant_db_path=self.plants)
        self.assertEqual(len(rows),1);self.assertTrue(rows[0]['test_data'])
        self.assertEqual(read_rows(self.archive,[self.mapping],plant_id=8,plant_db_path=self.plants),[])
        self.assertEqual(before,self.archive.read_bytes())
        self.commit({**self.batch,'records':[self.record('15')]})
        r=read_rows(self.archive,[self.mapping],plant_id=7,plant_db_path=self.plants)[0]
        self.assertEqual(r['status'],'conflict');self.assertIsNone(r['value'])
    def test_old_initial_boundary_is_flagged_without_deleting_original(self):
        self.mapping['test_data']=True
        self.batch['records']=[self.record()]
        # Simulate a legacy HA response with a synthetic initial state at window start.
        stamp=self.batch['records'][0]['ha_updated_at']
        self.batch['start']=stamp
        self.commit()
        before=self.archive.read_bytes()
        r=read_rows(self.archive,[self.mapping],plant_db_path=self.plants)[0]
        self.assertEqual(r['timing_kind'],'initial_state_uncertain')
        self.assertFalse(r['usable_for_timeline'])
        self.assertEqual(r['value'],'0')
        self.assertEqual(before,self.archive.read_bytes())

    def test_sync_opt_in_demo_and_failure(self):
        with patch('home_assistant_ui.load',side_effect=AssertionError('private')):
            with patch.dict('os.environ',{'BOTANEO_DEMO':'1'}):
                self.assertEqual(synchronize()['status'],'demo_disabled')
        self.assertEqual(synchronize(config=self.config)['status'],'disabled')
        cfg={**self.config,'sync_on_request':True}
        with patch('home_assistant_catchup.plan_catchup',side_effect=ValueError('fictitious')):
            self.assertEqual(synchronize(config=cfg,archive_path=self.archive,plant_db_path=self.plants)['status'],'failed')
    def test_sync_real_commit_and_second_pass_deduplicated(self):
        import json
        cfg={**self.config,'sync_on_request':True}
        state=self.record()['raw_state']
        class Response:
            status_code=200
            def iter_content(self,chunk_size):yield json.dumps([[state]]).encode()
            def close(self):pass
        args=dict(config=cfg,archive_path=self.archive,now='2026-10-15T07:00:00+00:00',plant_db_path=self.plants,requester=lambda *a,**k:Response())
        result=synchronize(**args)
        self.assertEqual(result['status'],'complete');self.assertEqual(result['facts_added'],1)
        result=synchronize(**args);self.assertEqual(result['facts_added'],0)


def descendants(p):
    for w in p.winfo_children():
        yield w
        yield from descendants(w)

class DashboardTests(unittest.TestCase):
    def test_dashboard_demo_and_small_windows(self):
        from home_assistant_dashboard import open_window
        root=tk.Tk();root.withdraw()
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with self.subTest(lang=lang,theme=palette['BG']),utiliser_langue(lang),patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch('home_assistant_ui.load',side_effect=AssertionError('private')),patch('home_assistant_view.read_rows',side_effect=AssertionError('archive')):
                        win=open_window(root,palette);win.geometry('560x440');win.update()
                        widgets=list(descendants(win));buttons={w.cget('text'):w for w in widgets if isinstance(w,tk.Button)}
                        self.assertEqual(buttons[t('ha_view_collect')].cget('state'),'disabled')
                        for key in ('ha_view_collect','ha_close','ha_test_title'):
                            b=buttons[t(key)];self.assertLessEqual(b.winfo_rooty()+b.winfo_height(),win.winfo_rooty()+win.winfo_height())
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
