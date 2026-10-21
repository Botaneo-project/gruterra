from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class PlantFilterTests(unittest.TestCase):
    def mappings(self):
        return [{'model':'Fictional','metric':'soil_moisture','hardware_id':'zigbee:0011223344556677','plant_id':7},
                {'model':'Fictional','metric':'soil_moisture','hardware_id':'zigbee:0011223344556688','plant_id':8},
                {'model':'Fictional','metric':'illuminance','hardware_id':'zigbee:0011223344556699'}]
    def test_plant_changes_rows_and_devices_without_keeping_wrong_sensor(self):
        from home_assistant_dashboard import open_window
        root=tk.Tk();root.withdraw()
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    rows=self.mappings()
                    with utiliser_langue(lang),patch('home_assistant_view.read_rows',return_value=[]) as read,patch('home_assistant_view.plants',return_value=[(7,'Même nom'),(8,'Même nom')]),patch('sensor_conversion_notes.load_notes',return_value=[]):
                        win=open_window(root,palette,config={'entities':rows});win.geometry('560x440');win.update()
                        widgets=list(descendants(win))
                        plant=next(w for w in widgets if isinstance(w,ttk.Combobox))
                        self.assertEqual(len(plant['values']),4)
                        self.assertNotEqual(plant['values'][1],plant['values'][2])
                        device=[w for w in widgets if isinstance(w,tk.OptionMenu)][1]
                        device['menu'].invoke(2);win.update()
                        self.assertEqual(read.call_args.args[1],[rows[1]])
                        plant.current(1);plant.event_generate('<<ComboboxSelected>>');win.update()
                        self.assertEqual(read.call_args.args[1],[rows[0]])
                        self.assertEqual(device['menu'].index('end'),1)
                        self.assertEqual(win.getvar(device.cget('textvariable')),t('ha_view_all_devices'))
                        plant.current(3);plant.event_generate('<<ComboboxSelected>>');win.update()
                        self.assertEqual(read.call_args.args[1],[rows[2]])
                        plant.current(0);plant.event_generate('<<ComboboxSelected>>');win.update()
                        self.assertEqual(read.call_args.args[1],rows)
                        close=next(w for w in widgets if isinstance(w,tk.Button) and w.cget('text')==t('ha_close'))
                        self.assertLessEqual(close.winfo_rooty()+close.winfo_height(),win.winfo_rooty()+win.winfo_height())
                        win.destroy()
        finally:root.destroy()
    def test_window_opened_for_one_plant_stays_scoped(self):
        from home_assistant_dashboard import open_window
        root=tk.Tk();root.withdraw()
        try:
            rows=self.mappings()
            with patch('home_assistant_view.read_rows',return_value=[]) as read,patch('home_assistant_view.plants',return_value=[]),patch('sensor_conversion_notes.load_notes',return_value=[]):
                win=open_window(root,THEME_CLAIR,plant_id=7,config={'entities':rows});win.update()
                plant=next(w for w in descendants(win) if isinstance(w,ttk.Combobox))
                self.assertEqual(str(plant.cget('state')),'disabled')
                self.assertEqual(len(plant['values']),1)
                self.assertEqual(read.call_args.args[1],[rows[0]])
                self.assertEqual(read.call_args.kwargs['plant_id'],7)
                win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
