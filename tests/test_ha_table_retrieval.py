from pathlib import Path
import sys
import tempfile
import tkinter as tk
from tkinter import ttk
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_dashboard import open_window
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class TableTests(unittest.TestCase):
    def test_availability_and_freshness_remain_distinct_from_value_and_test_label(self):
        now=datetime.now(timezone.utc)
        base={'hardware_id':'zigbee:0011223344556677','metric':'soil_moisture','ha_updated_at':now.isoformat(),
              'value':'0','unit':'%','status':'available','test_data':True,'timing_kind':'ha_state'}
        rows=[base,{**base,'value':None,'status':'unavailable'},{**base,'value':None,'status':'unknown'},
              {**base,'value':None,'status':'conflict'},
              {**base,'timing_kind':'ha_attribute_update','ha_value_changed_at':(now-timedelta(hours=3)).isoformat()},
              {**base,'ha_updated_at':(now+timedelta(hours=1)).isoformat(),'usable_for_timeline':False},
              {**base,'timing_kind':'initial_state_uncertain','usable_for_timeline':False}]
        root=tk.Tk();root.withdraw()
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with utiliser_langue(lang),patch('home_assistant_view.read_rows',return_value=rows),patch('home_assistant_view.plants',return_value=[]),patch('sensor_conversion_notes.load_notes',return_value=[]):
                        win=open_window(root,palette,config={'entities':[]});win.update()
                        table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview));items=table.get_children()
                        self.assertEqual(table.set(items[0],'value'),'0')
                        self.assertEqual(table.set(items[1],'value'),'—')
                        for index,key in ((0,'ha_state_available'),(1,'ha_state_unavailable'),(2,'ha_state_unknown'),(3,'ha_view_conflict')):
                            self.assertEqual(table.set(items[index],'availability'),t(key))
                        self.assertIn(t('ha_test_data'),table.set(items[3],'kind'))
                        for index,key in ((4,'ha_freshness_stale_state'),(5,'ha_freshness_future_state'),(6,'ha_freshness_initial_uncertain')):
                            self.assertEqual(table.set(items[index],'freshness'),t(key))
                        win.destroy()
        finally:root.destroy()

class RetrievalControlsTests(unittest.TestCase):
    def test_filters_restore_after_success_or_failure_and_close_cancels_poll(self):
        root=tk.Tk();root.withdraw()
        mapping={'hardware_id':'zigbee:0011223344556677','model':'fictional','metric':'soil_moisture'}
        try:
            for outcome in ('success','failure','close'):
                with tempfile.TemporaryDirectory() as directory:
                    workers=[]
                    result={'ok':outcome=='success','code':'complete','completed_windows':1,'facts_added':0,'revisions_added':0,'duplicates':0}
                    with patch('home_assistant_view.read_rows',return_value=[]),patch('home_assistant_view.plants',return_value=[]),patch('sensor_conversion_notes.load_notes',return_value=[]),patch('home_assistant_archive.checkpoint',return_value=None),patch('home_assistant_catchup.plan_catchup',return_value={'windows':[{'start':'fictional','end':'fictional'}]}),patch('home_assistant_catchup.run_catchup',return_value=result),patch('tkinter.messagebox.askyesno',return_value=True),patch('threading.Thread',side_effect=lambda target,daemon:SimpleNamespace(start=lambda:workers.append(target))):
                        win=open_window(root,THEME_CLAIR,config={'entities':[mapping]},archive_path=Path(directory)/'ha.db');win.update()
                        widgets=list(descendants(win));menus=[w for w in widgets if isinstance(w,tk.OptionMenu)]
                        plant=next(w for w in widgets if isinstance(w,ttk.Combobox))
                        button=next(w for w in widgets if isinstance(w,tk.Button) and w.cget('text')==t('ha_view_collect'))
                        baseline=len(root.tk.call('after','info'))
                        button.invoke();win.update()
                        self.assertEqual(len(workers),1)
                        self.assertTrue(all(str(w.cget('state'))=='disabled' for w in menus+[plant]))
                        if outcome=='close':
                            win.destroy();workers[0]();root.update()
                            done=tk.BooleanVar(root,value=False);root.after(180,lambda:done.set(True));root.wait_variable(done);root.update()
                            self.assertEqual(len(root.tk.call('after','info')),baseline)
                            continue
                        workers[0]()
                        done=tk.BooleanVar(root,value=False);root.after(180,lambda:done.set(True));root.wait_variable(done);win.update()
                        self.assertTrue(all(str(w.cget('state'))=='normal' for w in menus))
                        self.assertEqual(str(plant.cget('state')),'readonly')
                        self.assertEqual(button.cget('state'),'normal')
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
