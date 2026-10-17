"""Compact weather windows, fictional rows only; no network or private files."""
import sys,tkinter as tk,unittest
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE
import pluie_meteofrance as rain
import weather_view

def descendants(parent):
    for widget in parent.winfo_children():
        yield widget
        yield from descendants(widget)

class WeatherLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:cls.root=tk.Tk();cls.root.withdraw()
        except tk.TclError:raise unittest.SkipTest('Tk display unavailable')
    @classmethod
    def tearDownClass(cls):cls.root.destroy()
    def window(self,opener):
        before=set(self.root.winfo_children());opener()
        window=next(w for w in self.root.winfo_children() if w not in before)
        self.addCleanup(lambda:window.destroy() if window.winfo_exists() else None)
        window.geometry('620x440');window.update()
        return window
    def assert_inside(self,window,widget):
        self.assertTrue(widget.winfo_ismapped())
        self.assertGreaterEqual(widget.winfo_rootx(),window.winfo_rootx())
        self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),window.winfo_rootx()+window.winfo_width())
        self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),window.winfo_rooty()+window.winfo_height())
    def test_rain_controls_visible_in_both_languages(self):
        for language in ('fr','en'):
            for palette in (THEME_CLAIR,THEME_SOMBRE):
                with self.subTest(language=language,background=palette['BG']),utiliser_langue(language),patch.object(rain,'read',return_value=[]),patch.object(rain,'netatmo_snapshot',return_value=[]):
                    window=self.window(lambda:rain.open_window(self.root,palette))
                    widgets=list(descendants(window))
                    refresh=next(w for w in widgets if isinstance(w,tk.Button) and w.cget('text')==t('mf_rain_refresh'))
                    self.assert_inside(window,refresh)
                    self.assert_inside(window,next(w for w in widgets if isinstance(w,ttk.Combobox)))
                    self.assertEqual(window.cget('background'),palette['BG'])
                    window.destroy()
    def test_imported_weather_inherits_palette_and_keeps_actions_visible(self):
        for language in ('fr','en'):
            for palette in (THEME_CLAIR,THEME_SOMBRE):
                with self.subTest(language=language,background=palette['BG']),utiliser_langue(language),patch.object(weather_view,'observations',return_value=[]):
                    parent=tk.Toplevel(self.root);parent.configure(bg=palette['BG'])
                    self.addCleanup(lambda p=parent:p.destroy() if p.winfo_exists() else None)
                    weather_view.open_window(parent)
                    window=next(w for w in parent.winfo_children() if isinstance(w,tk.Toplevel))
                    window.geometry('620x440');window.update()
                    self.assertEqual(window.cget('background'),palette['BG'])
                    for button in (w for w in descendants(window) if isinstance(w,(tk.Button,ttk.Button))):self.assert_inside(window,button)
                    table=next(w for w in descendants(window) if isinstance(w,ttk.Treeview))
                    self.assertEqual(ttk.Style(window).lookup(table.cget('style'),'fieldbackground'),palette['CARD'])
                    window.destroy();parent.destroy()

    def test_home_assistant_toolbar_actions_remain_accessible(self):
        import home_assistant_ui as ui
        for language in ('fr','en'):
            with self.subTest(language=language),utiliser_langue(language),patch.object(ui,'load',return_value={'entities':[]}),patch.object(ui,'assess_mappings',return_value=[]):
                window=self.window(lambda:ui.open_window(self.root,THEME_SOMBRE))
                for button in (w for w in descendants(window) if isinstance(w,tk.Button)):
                    self.assert_inside(window,button)
                window.destroy()
