"""Real comparison dialogs on fictional local data, never on the user's base."""
from contextlib import ExitStack
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import database
import vue_historique as history
from i18n import utiliser_langue, traduire_courant as t
from ui_palette import history_palette
from ui_data_events import notifier_donnees_modifiees

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class ComparisonWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try: cls.root=tk.Tk(); cls.root.withdraw()
        except tk.TclError: raise unittest.SkipTest('Tk display unavailable')
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def fixture(self, stack, language='fr', dark=False):
        stack.enter_context(utiliser_langue(language))
        stack.enter_context(patch.object(history,'theme_actuel',return_value=history_palette(dark)))
        stack.enter_context(patch.object(database,'get_connection',side_effect=AssertionError('real database forbidden')))
        stack.enter_context(patch.object(database,'get_plante',return_value=(1,'Fictional plant')))
        rows=[(1,'2026-10-15T09:00:00',23,20,100,50,'',1),
              (2,'2026-10-15T10:00:00',24,25,200,50,'',1),
              (3,'2026-10-17T09:00:00',23,20,100,50,'',1),
              (4,'2026-10-17T10:00:00',24,25,300,50,'',1)]
        waters=[(1,1,'2026-10-15T08:00:00',40,'normal',None,None,'','',None,0),
                (2,1,'2026-10-17T08:00:00',40,'normal',None,None,'','',None,0)]
        measurement=stack.enter_context(patch.object(database,'get_mesures',side_effect=lambda **kw:list(rows)))
        watering=stack.enter_context(patch.object(database,'get_arrosages_plante',side_effect=lambda *a,**kw:list(waters)))
        for name in ('get_journal_plante','get_reperes_analyse_actifs'):
            stack.enter_context(patch.object(database,name,return_value=[]))
        self.errors=[]
        stack.enter_context(patch.object(self.root,'report_callback_exception',side_effect=lambda *args:self.errors.append(args[1])))
        parent=history.ouvrir_historique(self.root,1);parent.update()
        stack.callback(parent.destroy)
        return parent,rows,waters,measurement,watering

    def open_dialog(self, parent, key):
        before=set(parent.winfo_children())
        button=next(w for w in descendants(parent) if isinstance(w,ttk.Button) and w.cget('text')==t(key))
        button.invoke();parent.update()
        self.assertFalse(self.errors,self.errors)
        return next(w for w in parent.winfo_children() if isinstance(w,tk.Toplevel) and w not in before)

    def button(self, window, key):
        return next(w for w in descendants(window) if isinstance(w,ttk.Button) and w.cget('text')==t(key))

    def table(self, window, column):
        return next(w for w in descendants(window) if isinstance(w,ttk.Treeview) and column in w.cget('columns'))

    def values(self, table):
        return [table.item(item,'values') for item in table.get_children()]

    def test_compact_actions_and_scrolling_in_french_english_light_dark(self):
        scaling=float(self.root.tk.call('tk','scaling'))
        try:
            self.root.tk.call('tk','scaling',2.0)
            for language in ('fr','en'):
                for dark in (False,True):
                    with ExitStack() as stack:
                        parent,*_=self.fixture(stack,language,dark)
                        for key,size in (('compare_days','640x440'),('cycles','700x480')):
                            with self.subTest(language=language,dark=dark,window=key):
                                window=self.open_dialog(parent,key)
                                try:
                                    window.geometry(size);window.update()
                                    for action in ('compare_copy','refresh_plain','compare_close'):
                                        button=self.button(window,action)
                                        self.assertTrue(button.winfo_ismapped())
                                        self.assertGreaterEqual(button.winfo_rootx(),window.winfo_rootx())
                                        self.assertLessEqual(button.winfo_rootx()+button.winfo_width(),window.winfo_rootx()+window.winfo_width())
                                        self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),window.winfo_rooty()+window.winfo_height())
                                    tables=[w for w in descendants(window) if isinstance(w,ttk.Treeview)]
                                    for table in tables:
                                        self.assertTrue(table.cget('xscrollcommand'))
                                        self.assertTrue(table.cget('yscrollcommand'))
                                        self.assertIn('Gruterra',table.cget('style'))
                                    scroll=next(w for w in descendants(window) if isinstance(w,tk.Canvas) and w.find_all() and w.type(w.find_all()[0])=='window')
                                    self.assertLess(scroll.yview()[1],1)
                                    scroll.yview_moveto(1);window.update()
                                    report=next(w for w in descendants(window) if isinstance(w,tk.Text))
                                    self.assertLessEqual(report.winfo_rooty()+report.winfo_height(),scroll.winfo_rooty()+scroll.winfo_height())
                                    if key=='cycles':
                                        graph=next(w for w in descendants(window) if isinstance(w,tk.Canvas) and w.find_withtag('cycle_legend'))
                                        plot=graph.bbox('cycle_plot')
                                        for item in graph.find_withtag('cycle_legend'):
                                            left,top,right,bottom=graph.bbox(item)
                                            self.assertGreaterEqual(left,0)
                                            self.assertLessEqual(right,graph.winfo_width())
                                            self.assertLess(bottom,plot[1])
                                    self.assertFalse(self.errors,self.errors)
                                finally:window.destroy()
        finally:self.root.tk.call('tk','scaling',scaling)

    def test_days_refresh_and_copy_keep_the_selected_days(self):
        with ExitStack() as stack:
            parent,rows,*_=self.fixture(stack,'en')
            window=self.open_dialog(parent,'compare_days')
            combos=[w for w in descendants(window) if isinstance(w,ttk.Combobox)]
            choices=[w.get() for w in combos]
            table=self.table(window,'mesure')
            self.assertEqual(self.values(table)[0][1:3],('2','2'))
            selected_row=table.get_children()[-1];table.selection_set(selected_row)
            rows.append((5,'2026-10-17T11:00:00',24,23,350,50,'',1))
            notifier_donnees_modifiees(self.root);window.update()
            self.assertEqual([w.get() for w in combos],choices)
            self.assertEqual(self.values(table)[0][1:3],('3','2'))
            self.assertEqual(table.selection(),(selected_row,))
            self.button(window,'compare_copy').invoke()
            copied=window.clipboard_get()
            self.assertIn('17/10/2026',copied);self.assertIn('15/10/2026',copied)
            self.assertIn('Source: local database',copied)
            self.assertFalse(self.errors,self.errors)

    def test_cycle_selection_survives_new_fraction_and_new_latest_cycle(self):
        with ExitStack() as stack:
            parent,rows,waters,*_=self.fixture(stack)
            window=self.open_dialog(parent,'cycles')
            combos=[w for w in descendants(window) if isinstance(w,ttk.Combobox)]
            a,b,metric=combos
            metric.set(history.nom_serie_affiche('Lumière'));metric.event_generate('<<ComboboxSelected>>');window.update()
            before_b=b.get()
            table=self.table(window,'quantite')
            selected=table.get_children()[0];table.selection_set(selected)
            waters.append((3,1,'2026-10-17T08:10:00',55,'normal',None,None,'','',None,0))
            waters.append((4,1,'2026-10-18T08:00:00',30,'normal',None,None,'','',None,0))
            rows.append((5,'2026-10-18T09:00:00',24,23,400,50,'',1))
            notifier_donnees_modifiees(self.root);window.update()
            self.assertIn('17/10/2026',a.get());self.assertIn('95',a.get())
            self.assertEqual(b.get(),before_b)
            self.assertEqual(metric.get(),history.nom_serie_affiche('Lumière'))
            self.assertEqual(table.selection(),(selected,))
            self.assertEqual(len(table.get_children()),3)
            self.assertFalse(self.errors,self.errors)

    def test_failed_read_retains_view_and_copy_contains_stale_warning(self):
        for key,column in (('compare_days','mesure'),('cycles','quantite')):
            with self.subTest(window=key),ExitStack() as stack:
                parent,rows,waters,measurements,watering=self.fixture(stack)
                window=self.open_dialog(parent,key)
                table=self.table(window,column);before=self.values(table)
                watering.side_effect=OSError('fictional database unavailable')
                notifier_donnees_modifiees(self.root);window.update()
                self.assertEqual(self.values(table),before)
                self.button(window,'compare_copy').invoke()
                self.assertIn(t('history_refresh_failed'),window.clipboard_get())
                watering.side_effect=lambda *a,**kw:list(waters)
                self.button(window,'refresh_plain').invoke();window.update()
                self.button(window,'compare_copy').invoke()
                self.assertNotIn(t('history_refresh_failed'),window.clipboard_get())
                self.assertFalse(self.errors,self.errors)

    def test_removed_selection_does_not_leave_old_comparison_or_graph(self):
        for key in ('compare_days','cycles'):
            with self.subTest(window=key),ExitStack() as stack:
                parent,rows,waters,*_=self.fixture(stack)
                window=self.open_dialog(parent,key)
                if key=='compare_days':rows[:]=[r for r in rows if '2026-10-15' not in r[1]]
                else:waters.clear()
                notifier_donnees_modifiees(self.root);window.update()
                report=next(w for w in descendants(window) if isinstance(w,tk.Text))
                self.assertIn(t('history_choose_comparison'),report.get('1.0','end'))
                if key=='cycles':
                    table=self.table(window,'indicateur');self.assertFalse(table.get_children())
                    graphs=[w for w in descendants(window) if isinstance(w,tk.Canvas) and not any(w.type(item)=='window' for item in w.find_all())]
                    self.assertTrue(all(not graph.find_all() for graph in graphs))
                self.assertFalse(self.errors,self.errors)

    def test_initial_read_error_is_reported_without_partial_dialog(self):
        for key in ('compare_days','cycles'):
            with self.subTest(window=key),ExitStack() as stack:
                parent,rows,waters,measurements,watering=self.fixture(stack)
                before=set(parent.winfo_children())
                watering.side_effect=OSError('fictional inaccessible data')
                with patch.object(history.messagebox,'showerror') as error:
                    self.button(parent,key).invoke();parent.update()
                    error.assert_called_once()
                    self.assertIn(t('history_read_failed'),error.call_args.args)
                self.assertEqual(before,set(parent.winfo_children()))
                self.assertFalse(self.errors,self.errors)

    def test_empty_data_is_information_not_an_exception(self):
        for key in ('compare_days','cycles'):
            with self.subTest(window=key),ExitStack() as stack:
                parent,rows,waters,*_=self.fixture(stack)
                rows.clear();waters.clear()
                with patch.object(history.messagebox,'showinfo') as info:
                    self.button(parent,key).invoke();parent.update()
                    info.assert_called_once()
                self.assertFalse(self.errors,self.errors)

    def test_resizing_cycle_graph_preserves_report_scroll_and_table_selection(self):
        with ExitStack() as stack:
            parent,*_=self.fixture(stack)
            window=self.open_dialog(parent,'cycles');window.geometry('700x480');window.update()
            table=self.table(window,'indicateur')
            selected=table.get_children()[-1];table.selection_set(selected)
            report=next(w for w in descendants(window) if isinstance(w,tk.Text))
            report.yview_moveto(1);window.update();before=report.yview()
            window.geometry('900x600');window.update()
            self.assertEqual(table.selection(),(selected,))
            # Width changes the number of wrapped lines, hence the fraction.
            # The reader must stay at the end rather than jumping back to the top.
            self.assertEqual(report.yview()[1],before[1])
            self.assertGreater(report.yview()[0],0.5)
            self.assertFalse(self.errors,self.errors)
