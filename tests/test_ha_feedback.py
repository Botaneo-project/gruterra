from pathlib import Path
import sys
import unittest
import tkinter as tk
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_feedback import failure_message
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class FailureFeedbackTests(unittest.TestCase):
    def test_http_and_saved_progress_are_translated_without_raw_error(self):
        for language in ('fr','en'):
            with utiliser_langue(language):
                for status,key in ((401,'ha_failure_access'),(403,'ha_failure_access'),(429,'ha_failure_rate'),(503,'ha_failure_server')):
                    text=failure_message({'http_status':status,'completed_windows':2,'error':'PRIVATE','code':'PRIVATE','body':'PRIVATE'})
                    self.assertIn(t(key),text)
                    self.assertIn(str(status),text)
                    self.assertIn(t('ha_failure_preserved').format(windows=2),text)
                    self.assertNotIn('PRIVATE',text)
                self.assertEqual(failure_message({'code':'PRIVATE','http_status':'PRIVATE','completed_windows':'PRIVATE'}),t('ha_view_failed'))
    def test_specific_safe_reasons_and_malformed_result(self):
        for reason,key in (('history_too_large','ha_failure_dense'),('mapping_not_authorized','ha_failure_mapping'),('history_connection_failed','ha_failure_connection')):
            self.assertEqual(failure_message({'reason':reason}),t(key))
        self.assertEqual(failure_message(None),t('ha_view_failed'))
        self.assertNotIn('999999',failure_message({'http_status':999999,'completed_windows':999999}))

class MappingDisplayTests(unittest.TestCase):
    def test_manual_recovery_bounds_old_checkpoint_without_skipping(self):
        import home_assistant_catchup_ui as ui
        from datetime import datetime,timedelta,timezone
        saved=(datetime.now(timezone.utc)-timedelta(days=20)).isoformat()
        root=tk.Tk();root.withdraw()
        try:
            with patch('home_assistant_ui.load',return_value={}),patch('home_assistant_archive.checkpoint',return_value=saved),patch('home_assistant_catchup.plan_catchup',return_value={'windows':[]}) as plan:
                win=ui.open_window(root,THEME_CLAIR);win.update()
                button=next(w for w in descendants(win) if isinstance(w,tk.Button) and w.cget('text')==t('ha_catchup_plan'))
                button.invoke();win.update()
                args=plan.call_args.kwargs
                self.assertEqual(args['start'],saved)
                self.assertEqual(datetime.fromisoformat(args['end'])-datetime.fromisoformat(saved),timedelta(days=7))
                win.destroy()
        finally:root.destroy()

    def test_settings_show_associated_plant_and_unassigned_in_both_themes(self):
        import home_assistant_ui as ui
        root=tk.Tk();root.withdraw()
        try:
            for language in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    cfg={'entities':[{'entity_id':'sensor.test_soil','metric':'soil_moisture','plant_id':7},
                                     {'entity_id':'sensor.test_air','metric':'air_humidity'}]}
                    with utiliser_langue(language),patch.object(ui,'load',return_value=cfg),patch.object(ui,'assess_mappings',return_value=['identity_pending']*2),patch('home_assistant_view.plants',return_value=[(7,'Crassula fictive')]):
                        win=ui.open_window(root,palette);win.geometry('620x440');win.update()
                        from tkinter import ttk
                        table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
                        values=[table.item(row,'values') for row in table.get_children()]
                        self.assertEqual(table.heading('plant','text'),t('ha_view_plant'))
                        self.assertEqual(values[0][0],'Crassula fictive')
                        self.assertEqual(values[1][0],t('ha_view_unassigned'))
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
