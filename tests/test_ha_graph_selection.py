from pathlib import Path
import sys
import sqlite3
import tempfile
import unittest
from contextlib import closing
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from home_assistant_archive import commit_history
from home_assistant_view import read_rows
from home_assistant_sensors import prepare

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.plants=Path(self.tmp.name)/'plants.db';self.archive=Path(self.tmp.name)/'ha.db'
        with closing(sqlite3.connect(self.plants)) as db,db:db.execute('CREATE TABLE capteurs (adresse_ble TEXT)')
        self.light={'entity_id':'sensor.light','device_id':'fictional','model':'fictional','metric':'illuminance','hardware_id':'zigbee:0011223344556677','hardware_confirmed':True,'plant_id':1}
        self.soil={**self.light,'entity_id':'sensor.soil','metric':'soil_moisture'}
        self.cfg={'schema_version':1,'enabled':True,'base_url':'https://example.invalid','access_token':'fictional','instance_id':'fictional','entities':[self.light,self.soil]}
        def record(mapping,stamp):
            state={'entity_id':mapping['entity_id'],'state':'16','attributes':{'unit_of_measurement':'lx' if mapping['metric']=='illuminance' else '%'},'last_updated':stamp,'last_changed':stamp}
            return prepare(state,mapping,instance_id='fictional',received_at='2026-10-20T06:00:00Z')
        records=[record(self.soil,f'2026-10-20T0{h}:00:00Z') for h in (1,2,3,4)]
        records += [record(self.light,f'2026-10-20T05:00:{sec:02}Z') for sec in range(10)]
        records += [record(self.soil,'2026-10-20T02:00:00.100000Z'),record(self.soil,'2026-10-20T02:00:00.200000Z')]
        commit_history(self.archive,self.cfg,{'ok':True,'http_status':200,'records':records,'start':'2026-10-20T00:00:00Z','end':'2026-10-20T06:00:00Z'},plant_db_path=self.plants)
    def read(self,**kwargs):
        return read_rows(self.archive,self.cfg['entities'],plant_db_path=self.plants,**kwargs)
    def test_busy_light_cannot_hide_selected_soil(self):
        before=self.archive.read_bytes()
        self.assertTrue(all(row['metric']=='illuminance' for row in self.read(limit=3)))
        rows=self.read(metric='soil_moisture',limit=3)
        self.assertEqual(len(rows),3);self.assertTrue(all(row['metric']=='soil_moisture' for row in rows))
        self.assertEqual(self.archive.read_bytes(),before)
    def test_period_applies_before_limit_and_respects_subsecond_end(self):
        rows=self.read(metric='soil_moisture',start='2026-10-20T03:00:00+02:00',end='2026-10-20T04:00:00.200000+02:00',limit=1)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['ha_updated_at'],'2026-10-20T02:00:00.100000+00:00')
    def test_metric_filter_respects_plant_and_rejects_invalid_quantity(self):
        self.assertEqual(self.read(metric='soil_moisture',plant_id=2),[])
        with self.assertRaisesRegex(ValueError,'unsupported_metric'):self.read(metric='unknown')

class DashboardSelectionTests(unittest.TestCase):
    def test_filter_selects_exact_physical_device_even_with_same_suffix(self):
        import tkinter as tk
        from home_assistant_dashboard import open_window
        from ui_palette import THEME_CLAIR
        root=tk.Tk();root.withdraw()
        def descendants(parent):
            for child in parent.winfo_children():
                yield child
                yield from descendants(child)
        mappings=[{'model':'Fictitious','hardware_id':'zigbee:0011223344556677','metric':'soil_moisture'},
                  {'model':'Fictitious','hardware_id':'zigbee:9911223344556677','metric':'soil_moisture'}]
        try:
            with patch('home_assistant_view.read_rows',return_value=[]) as read,patch('home_assistant_view.plants',return_value=[]),patch('sensor_conversion_notes.load_notes',return_value=[]):
                win=open_window(root,THEME_CLAIR,config={'entities':mappings});win.update()
                menus=[w for w in descendants(win) if isinstance(w,tk.OptionMenu)]
                labels=[menus[1]['menu'].entrycget(i,'label') for i in (1,2)]
                self.assertNotEqual(labels[0],labels[1])
                menus[1]['menu'].invoke(2);win.update()
                self.assertEqual(read.call_args.args[1],[mappings[1]])
                self.assertEqual(read.call_args.kwargs['metric'],'soil_moisture')
                win.destroy()
        finally:root.destroy()

    def test_demo_quantity_changes_both_graph_selection_and_table(self):
        import tkinter as tk
        from tkinter import ttk
        from home_assistant_dashboard import open_window
        from i18n import utiliser_langue,traduire_courant as t
        from ui_palette import THEME_CLAIR,THEME_SOMBRE
        def descendants(parent):
            for child in parent.winfo_children():
                yield child
                yield from descendants(child)
        root=tk.Tk();root.withdraw()
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with utiliser_langue(lang),patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch('home_assistant_ui.load',side_effect=AssertionError('private')),patch('home_assistant_view.read_rows',side_effect=AssertionError('real archive')):
                        win=open_window(root,palette);win.update()
                        widgets=list(descendants(win))
                        table=next(w for w in widgets if isinstance(w,ttk.Treeview))
                        self.assertEqual(len(table.get_children()),13)
                        selector=next(w for w in widgets if isinstance(w,tk.OptionMenu))
                        selector['menu'].invoke(3);win.update()
                        self.assertEqual(len(table.get_children()),12)
                        self.assertTrue(all(table.item(row,'values')[3]==t('ha_metric_illuminance') for row in table.get_children()))
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
