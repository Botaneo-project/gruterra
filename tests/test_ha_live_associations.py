from pathlib import Path
import sys
import copy
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from ui_palette import THEME_CLAIR
from i18n import traduire_courant as t

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class LiveAssociationTests(unittest.TestCase):
    def config(self,plant):
        return {'entities':[{'entity_id':'sensor.fictional_soil','device_id':'fictional','model':'fictional',
                             'hardware_id':'zigbee:0011223344556677','metric':'soil_moisture','plant_id':plant}]}
    def test_settings_save_refreshes_global_and_plant_windows(self):
        import home_assistant_ui as ui
        from home_assistant_dashboard import open_window
        state={'config':self.config(7)};root=tk.Tk();root.geometry('120x80');root.update()
        def save(*args,**kwargs):state['config']=self.config(8);return copy.deepcopy(state['config'])
        try:
            with patch.object(ui,'load',side_effect=lambda:copy.deepcopy(state['config'])),patch.object(ui,'save_config',side_effect=save),patch.object(ui,'assess_mappings',return_value=['authorized']),patch('home_assistant_view.plants',return_value=[(7,'Fictional A'),(8,'Fictional B')]),patch('home_assistant_view.read_rows',return_value=[]) as read,patch('sensor_conversion_notes.load_notes',return_value=[]):
                global_win=open_window(root,THEME_CLAIR);locked_win=open_window(root,THEME_CLAIR,plant_id=7)
                settings=ui.open_window(root,THEME_CLAIR);root.update()
                plant=next(w for w in descendants(global_win) if isinstance(w,ttk.Combobox))
                plant.current(1);plant.event_generate('<<ComboboxSelected>>');root.update()
                read.reset_mock()
                button=next(w for w in descendants(settings) if isinstance(w,tk.Button) and w.cget('text')==t('ha_save'))
                button.invoke();root.update()
                self.assertEqual(plant.current(),0)
                self.assertIn('8 — Fictional B',plant['values'])
                calls=read.call_args_list
                self.assertTrue(any(call.kwargs['plant_id']==7 and call.args[1]==[] for call in calls))
                self.assertTrue(any(call.kwargs['plant_id'] is None and call.args[1][0]['plant_id']==8 for call in calls if call.args[1]))
                settings.destroy();locked_win.destroy();global_win.destroy()
        finally:root.destroy()
    def test_unreadable_changed_config_blocks_collection_without_using_old_settings(self):
        import home_assistant_ui as ui
        from home_assistant_dashboard import open_window
        root=tk.Tk();root.withdraw()
        try:
            with patch.object(ui,'load',return_value=self.config(7)) as load,patch('home_assistant_view.plants',return_value=[]),patch('home_assistant_view.read_rows',return_value=[]),patch('sensor_conversion_notes.load_notes',return_value=[]),patch('home_assistant_catchup.plan_catchup') as plan:
                win=open_window(root,THEME_CLAIR);win.update()
                load.side_effect=ValueError('fictional unreadable')
                button=next(w for w in descendants(win) if isinstance(w,tk.Button) and w.cget('text')==t('ha_view_collect'))
                button.invoke();win.update()
                plan.assert_not_called()
                self.assertEqual(button.cget('state'),'disabled')
                self.assertTrue(any(w.getvar(w.cget('textvariable'))==t('ha_config_unreadable') for w in descendants(win) if isinstance(w,tk.Label) and w.cget('textvariable')))
                win.destroy()
        finally:root.destroy()
    def test_home_summary_refreshes_and_removes_binding_and_timer_on_close(self):
        import home_assistant_summary as summary
        from ui_data_events import notifier_associations_modifiees
        root=tk.Tk();root.geometry('500x300');root.update()
        try:
            with patch.object(summary,'load_summary',return_value={'ok':True,'devices':[]}) as load:
                frame=summary.card(root,THEME_CLAIR);root.update()
                original_timers=len(root.tk.call('after','info'))
                self.assertEqual(load.call_count,1)
                notifier_associations_modifiees(root);root.update()
                self.assertEqual(load.call_count,2)
                self.assertEqual(len(root.tk.call('after','info')),original_timers)
                frame.destroy();root.update()
                self.assertFalse(root.bind('<<GruterraAssociationsChanged>>'))
                notifier_associations_modifiees(root);root.update()
                self.assertEqual(load.call_count,2)
        finally:root.destroy()

if __name__=='__main__':unittest.main()
