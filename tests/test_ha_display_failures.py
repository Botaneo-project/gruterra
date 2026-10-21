from pathlib import Path
from datetime import datetime,timezone
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

class DisplayFailureTests(unittest.TestCase):
    def test_failed_filter_read_clears_old_values_and_recovers_on_next_read(self):
        from home_assistant_dashboard import open_window
        root=tk.Tk();root.withdraw()
        stamp=datetime.now(timezone.utc).isoformat()
        soil={'hardware_id':'zigbee:0011223344556677','metric':'soil_moisture','ha_updated_at':stamp,'value':'16','unit':'%','status':'available'}
        air={**soil,'metric':'air_humidity','value':'58'}
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with utiliser_langue(lang),patch('home_assistant_view.read_rows',side_effect=[[soil],OSError('FICTIONAL PRIVATE DETAIL'),[air]]),patch('home_assistant_view.plants',return_value=[]),patch('sensor_conversion_notes.load_notes',return_value=[]):
                        win=open_window(root,palette,config={'entities':[]});win.update()
                        table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
                        canvas=next(w for w in descendants(win) if isinstance(w,tk.Canvas) and any(w.type(item)=='text' and t('ha_metric_soil_moisture') in w.itemcget(item,'text') for item in w.find_all()))
                        menu=next(w for w in descendants(win) if isinstance(w,tk.OptionMenu))
                        self.assertEqual(len(table.get_children()),1)
                        menu['menu'].invoke(1);win.update()
                        self.assertEqual(table.get_children(),())
                        texts=[canvas.itemcget(item,'text') for item in canvas.find_all() if canvas.type(item)=='text']
                        self.assertIn(t('ha_view_failed'),texts)
                        self.assertFalse(any('FICTIONAL PRIVATE' in text for text in texts))
                        win.geometry('620x500');win.update()
                        self.assertIn(t('ha_view_failed'),[canvas.itemcget(item,'text') for item in canvas.find_all() if canvas.type(item)=='text'])
                        menu['menu'].invoke(1);win.update()
                        self.assertEqual(table.set(table.get_children()[0],'value'),'58')
                        self.assertEqual(table.set(table.get_children()[0],'metric'),t('ha_metric_air_humidity'))
                        win.destroy()
        finally:root.destroy()
    def test_many_device_legends_leave_a_positive_plot_area(self):
        from home_assistant_chart import draw_chart
        root=tk.Tk();root.withdraw()
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with utiliser_langue(lang):
                        win=tk.Toplevel(root);win.geometry('560x1000')
                        canvas=tk.Canvas(win,width=560,height=340);canvas.pack(fill='x');win.update()
                        rows=[{'hardware_id':f'zigbee:{index:016x}','metric':'soil_moisture','value':str(10+index%10),
                               'ha_updated_at':'2026-10-20T12:00:00+00:00','status':'available'} for index in range(60)]
                        draw_chart(canvas,rows,'soil_moisture',palette,t);win.update()
                        draw_chart(canvas,rows,'soil_moisture',palette,t)
                        legends=[canvas.bbox(item) for item in canvas.find_all() if canvas.type(item)=='text' and canvas.itemcget(item,'text').startswith('zigbee:')]
                        self.assertEqual(len(legends),60)
                        bottom=max(box[3] for box in legends)
                        dots=[canvas.coords(item) for item in canvas.find_all() if canvas.type(item)=='oval' and round(canvas.coords(item)[2]-canvas.coords(item)[0])==6]
                        self.assertEqual(len(dots),60)
                        self.assertTrue(all((coords[1]+coords[3])/2>bottom+15 for coords in dots))
                        self.assertTrue(all((coords[1]+coords[3])/2<canvas.winfo_height()-48 for coords in dots))
                        draw_chart(canvas,rows[:1],'soil_moisture',palette,t);win.update()
                        self.assertEqual(int(float(canvas.cget('height'))),340)
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
