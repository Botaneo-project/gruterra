"""Real Tk history on fictional readings, no real database allowed."""
from contextlib import ExitStack
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'_app'))
import database
import vue_historique as history
from i18n import utiliser_langue, traduire_courant as t
from ui_data_events import notifier_donnees_modifiees
from ui_palette import history_palette

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

class HistoryRefreshLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root=tk.Tk(); cls.root.withdraw()
        except tk.TclError:
            raise unittest.SkipTest('Tk display unavailable')
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def fixture(self, stack):
        rows=[(1,'2026-10-17T08:00:00',20,23,100,50,None,1),
              (2,'2026-10-18T08:00:00',21,24,200,50,None,1)]
        stack.enter_context(patch.object(database,'get_connection',side_effect=AssertionError('real database forbidden')))
        stack.enter_context(patch.object(database,'get_plante',return_value=(1,'Fictional plant')))
        measurements=stack.enter_context(patch.object(database,'get_mesures',side_effect=lambda **kw:list(rows)))
        for name in ('get_arrosages_plante','get_journal_plante','get_reperes_analyse_actifs'):
            stack.enter_context(patch.object(database,name,return_value=[]))
        return rows, measurements

    def test_actions_visible_and_body_scrolls_in_both_languages_and_themes(self):
        scaling=float(self.root.tk.call('tk','scaling'))
        try:
            self.root.tk.call('tk','scaling',2.0)
            for language in ('fr','en'):
                for dark in (False,True):
                    with self.subTest(language=language,dark=dark), ExitStack() as stack:
                        stack.enter_context(utiliser_langue(language))
                        stack.enter_context(patch.object(history,'theme_actuel',return_value=history_palette(dark)))
                        self.fixture(stack)
                        win=history.ouvrir_historique(self.root,1)
                        try:
                            win.geometry('860x600');win.update()
                            buttons=[w for w in descendants(win) if isinstance(w,ttk.Button)]
                            for key in ('refresh_plain','copy_day','copy_summary','compare_days','cycles','normal_order','lighting_close'):
                                button=next(w for w in buttons if w.cget('text')==t(key))
                                self.assertTrue(button.winfo_ismapped(),key)
                                self.assertGreaterEqual(button.winfo_rootx(),win.winfo_rootx(),key)
                                self.assertLessEqual(button.winfo_rootx()+button.winfo_width(),win.winfo_rootx()+win.winfo_width(),key)
                                self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),win.winfo_rooty()+win.winfo_height(),key)
                            scroll=next(w for w in descendants(win) if isinstance(w,tk.Canvas) and w.find_withtag('all') and w.type(w.find_all()[0])=='window')
                            self.assertLess(scroll.yview()[1],1)
                            scroll.yview_moveto(1);win.update()
                            table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
                            self.assertLessEqual(table.winfo_rooty()+table.winfo_height(),scroll.winfo_rooty()+scroll.winfo_height())
                        finally:win.destroy()
        finally:self.root.tk.call('tk','scaling',scaling)

    def test_compact_filters_light_first_and_readable_fields(self):
        for language in ('fr','en'):
            for dark in (False,True):
                with self.subTest(language=language,dark=dark), ExitStack() as stack:
                    stack.enter_context(utiliser_langue(language))
                    palette=history_palette(dark)
                    stack.enter_context(patch.object(history,'theme_actuel',return_value=palette))
                    self.fixture(stack)
                    win=history.ouvrir_historique(self.root,1,lambda:None)
                    try:
                        win.geometry('860x600');win.update()
                        combos=[w for w in descendants(win) if isinstance(w,ttk.Combobox)]
                        light=history.nom_serie_affiche('Lumière')
                        series=next(w for w in combos if light in w.cget('values'))
                        self.assertEqual(series.get(),light)
                        self.assertEqual(series.cget('values')[0],light)
                        for combo in combos:
                            self.assertLessEqual(combo.winfo_rootx()+combo.winfo_width(),win.winfo_rootx()+win.winfo_width())
                            style=ttk.Style(combo);name=combo.cget('style')
                            self.assertEqual(style.lookup(name,'foreground',('readonly',)),palette['TEXT'])
                            self.assertEqual(style.lookup(name,'fieldbackground',('readonly',)),palette['CARD'])
                            self.assertIn('Gruterra',style.layout(name)[0][0])
                        self.assertLess(max(c.winfo_rooty() for c in combos)-min(c.winfo_rooty() for c in combos),8)
                    finally:win.destroy()

    def test_import_refresh_preserves_selected_day_measurement_and_row(self):
        with ExitStack() as stack:
            stack.enter_context(utiliser_langue('en'))
            rows,_=self.fixture(stack)
            win=history.ouvrir_historique(self.root,1)
            try:
                win.update()
                combos=[w for w in descendants(win) if isinstance(w,ttk.Combobox)]
                day=next(w for w in combos if '18/10/2026' in w.cget('values'))
                day.set('18/10/2026');day.event_generate('<<ComboboxSelected>>');win.update()
                table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
                item=table.get_children()[0];old_values=table.item(item,'values');table.selection_set(item)
                rows.append((3,'2026-10-18T09:00:00',21,24,250,50,None,1))
                notifier_donnees_modifiees(self.root);win.update()
                self.assertEqual(day.get(),'18/10/2026')
                self.assertEqual(len(table.get_children()),2)
                self.assertEqual(table.item(table.selection()[0],'values'),old_values)
                self.assertTrue(any(t('history_freshness').split('{')[0] in str(w.cget('text')) for w in descendants(win) if isinstance(w,tk.Label)))
                win.destroy();notifier_donnees_modifiees(self.root);self.root.update()
            finally:
                if win.winfo_exists():win.destroy()

    def test_refresh_error_retains_old_data_and_marks_it_stale(self):
        with ExitStack() as stack:
            stack.enter_context(utiliser_langue('fr'))
            rows,measurements=self.fixture(stack)
            win=history.ouvrir_historique(self.root,1)
            try:
                win.update();table=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
                before=[table.item(i,'values') for i in table.get_children()]
                measurements.side_effect=OSError('invented database unavailable')
                notifier_donnees_modifiees(self.root);win.update()
                self.assertEqual(before,[table.item(i,'values') for i in table.get_children()])
                labels=[w for w in descendants(win) if isinstance(w,tk.Label)]
                self.assertTrue(any(w.cget('text')==t('history_refresh_failed') for w in labels))
            finally:win.destroy()

    def test_graph_does_not_join_readings_across_long_gaps(self):
        with ExitStack() as stack:
            stack.enter_context(utiliser_langue('fr'))
            rows,_=self.fixture(stack)
            rows[:]=[(1,'2026-10-17T08:00:00',20,23,100,50,None,1),
                     (2,'2026-10-17T09:00:00',21,24,200,50,None,1),
                     (3,'2026-10-18T08:00:00',21,24,250,50,None,1),
                     (4,'2026-10-18T09:00:00',21,24,270,50,None,1)]
            win=history.ouvrir_historique(self.root,1)
            try:
                win.update()
                graph=next(w for w in descendants(win) if isinstance(w,tk.Canvas) and w.find_withtag('measurement_line'))
                lines=graph.find_withtag('measurement_line')
                self.assertEqual(len(lines),2)
                self.assertTrue(all(graph.itemcget(item,'smooth')=='0' for item in lines))
            finally:win.destroy()
