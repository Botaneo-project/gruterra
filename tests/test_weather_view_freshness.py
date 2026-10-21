"""Weather views on fictional SQLite data; no network or user configuration."""
import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
from contextlib import closing
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_app'))
import weather_view
import weather_protocol as protocol
from weather_store import import_batch
from ui_data_events import notifier_donnees_modifiees
from ui_palette import THEME_CLAIR,THEME_SOMBRE
from i18n import utiliser_langue,traduire_courant as t

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class WeatherViewFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:cls.root=tk.Tk();cls.root.withdraw()
        except tk.TclError:raise unittest.SkipTest('Tk display unavailable')
    @classmethod
    def tearDownClass(cls):cls.root.destroy()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'fictional-weather.sqlite3'
        self.batch=json.loads((ROOT/'EXEMPLE_METEO_LOT_V1.json').read_text(encoding='utf-8'))
        self.errors=[]
        mock=patch.object(self.root,'report_callback_exception',side_effect=lambda *args:self.errors.append(args[1]))
        mock.start();self.addCleanup(mock.stop)
    def window(self,palette=THEME_CLAIR):
        win=weather_view.open_window(self.root,self.path,palette)
        self.addCleanup(lambda:win.destroy() if win.winfo_exists() else None)
        win.geometry('620x360');win.update()
        table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
        return win,table
    def labels(self,win):
        return '\n'.join(str(w.cget('text')) for w in descendants(win) if isinstance(w,tk.Label))
    def sign(self,row):
        obs=row['observation']
        row['observation_id']='w1_'+protocol.checksum({key:obs[key] for key in protocol.IDENTITY_KEYS})
        row['revision_hash']=protocol.checksum(obs)
        return row
    def test_import_updates_open_view_and_retains_selected_observation(self):
        with utiliser_langue('fr'):
            import_batch(self.path,self.batch,'pi-fictif')
            win,table=self.window()
            first=table.get_children()[0];table.selection_set(first);table.xview_moveto(0.5)
            second=copy.deepcopy(self.batch['rows'][0]);second['observation']['source_time']='2026-10-11T10:00:00Z';second['retrieved_at']='2026-10-11T10:00:01Z';self.sign(second)
            import_batch(self.path,{**self.batch,'rows':[second]},'pi-fictif')
            notifier_donnees_modifiees(self.root);win.update()
            self.assertEqual(len(table.get_children()),2)
            self.assertEqual(table.selection(),(first,))
            self.assertGreater(table.xview()[0],0)
            self.assertIn(second['retrieved_at'],self.labels(win))
            self.assertIn(t('history_local_read').split('{')[0],self.labels(win))
            self.assertFalse(self.errors,self.errors)
    def test_zero_null_and_unknown_source_time_remain_distinct(self):
        with utiliser_langue('en'):
            zero=copy.deepcopy(self.batch['rows'][0]);zero['observation']['value']='0';self.sign(zero)
            absent=copy.deepcopy(zero);absent['observation'].update(value=None,source_time=None,time_precision='unknown',temporal_quality='missing_timestamp');self.sign(absent);absent['observation_id']='wu1_'+str(uuid4())
            import_batch(self.path,{**self.batch,'rows':[zero,absent],'pending':2},'pi-fictif')
            win,table=self.window()
            values=[table.item(item,'values') for item in table.get_children()]
            self.assertEqual({row[4] for row in values},{'0',t('weather_pi_missing')})
            missing=next(row for row in values if row[4]==t('weather_pi_missing'))
            self.assertEqual(missing[6],t('weather_source_date_unknown'))
            self.assertFalse(self.errors,self.errors)
    def test_render_failure_preserves_whole_previous_view_then_recovers(self):
        with utiliser_langue('fr'):
            import_batch(self.path,self.batch,'pi-fictif')
            win,table=self.window();before=[table.item(i,'values') for i in table.get_children()]
            real=weather_view.observations(self.path)
            with patch.object(weather_view,'observations',return_value=[*real,{'period':{}}]):
                notifier_donnees_modifiees(self.root);win.update()
            self.assertEqual(before,[table.item(i,'values') for i in table.get_children()])
            self.assertIn(t('weather_pi_view_stale'),self.labels(win))
            notifier_donnees_modifiees(self.root);win.update()
            self.assertNotIn(t('weather_pi_view_stale'),self.labels(win))
            self.assertFalse(self.errors,self.errors)
    def test_malformed_stored_json_has_explicit_error_and_keeps_old_rows(self):
        with utiliser_langue('fr'):
            import_batch(self.path,self.batch,'pi-fictif');win,table=self.window()
            before=table.get_children()
            with closing(sqlite3.connect(self.path)) as db,db:
                db.execute('UPDATE weather_observations_v1 SET observation_json=?',('{}',))
            notifier_donnees_modifiees(self.root);win.update()
            self.assertEqual(table.get_children(),before)
            self.assertIn(t('weather_pi_view_stale'),self.labels(win))
            self.assertFalse(self.errors,self.errors)
    def test_empty_view_does_not_create_database_or_imply_no_rain(self):
        with utiliser_langue('fr'):
            win,table=self.window()
            self.assertFalse(table.get_children());self.assertFalse(self.path.exists())
            self.assertIn(t('weather_pi_no_imported_data'),self.labels(win))
    def test_compact_actions_visible_with_large_text_and_long_status(self):
        scaling=float(self.root.tk.call('tk','scaling'))
        try:
            self.root.tk.call('tk','scaling',2.0)
            import_batch(self.path,self.batch,'pi-fictif')
            for language in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with self.subTest(language=language,palette=palette['BG']),utiliser_langue(language):
                        win,table=self.window(palette)
                        for button in (w for w in descendants(win) if isinstance(w,tk.Button)):
                            self.assertTrue(button.winfo_ismapped())
                            self.assertLessEqual(button.winfo_rootx()+button.winfo_width(),win.winfo_rootx()+win.winfo_width())
                            self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),win.winfo_rooty()+win.winfo_height())
                        self.assertGreater(table.winfo_height(),40)
                        self.assertFalse(self.errors,self.errors)
                        win.destroy()
        finally:self.root.tk.call('tk','scaling',scaling)
