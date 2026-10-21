"""Local contribution window geometry, no real identity or server access."""
from pathlib import Path
import os
import sys
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'_app').exists(): ROOT=Path('C:/Plantes')
sys.path.insert(0,str(ROOT/'_app'))
import contribution_locale as information
import contribution_suivi as tracking
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class ContributionWindowTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.root.withdraw()
        self.scaling=self.root.tk.call('tk','scaling');self.root.tk.call('tk','scaling',2.0)
    def tearDown(self):
        self.root.tk.call('tk','scaling',self.scaling);self.root.destroy()
    def check_close(self,win):
        button=next(w for w in descendants(win) if isinstance(w,tk.Button) and w.cget('text')==t('close'))
        self.assertGreater(button.winfo_height(),10)
        self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),win.winfo_rooty()+win.winfo_height())
    def test_information_controls_and_explanation_are_accessible(self):
        for lang in ('fr','en'):
            for palette in (THEME_CLAIR,THEME_SOMBRE):
                with self.subTest(lang=lang,theme=palette['BG']),utiliser_langue(lang),patch.dict(os.environ,{'BOTANEO_DEMO':'0'}),patch.object(information,'marquer_information_lue') as record:
                    win=information.ouvrir_information(self.root,palette);win.geometry('440x320');win.update()
                    self.check_close(win)
                    widgets=list(descendants(win));canvas=next(w for w in widgets if isinstance(w,tk.Canvas))
                    canvas.yview_moveto(1);win.update()
                    self.assertGreater(canvas.yview()[0],0)
                    for key in ('contribution_backup_key','contribution_restore_key','contribution_tracking_title'):
                        button=next(w for w in widgets if isinstance(w,tk.Button) and w.cget('text')==t(key))
                        self.assertLessEqual(button.winfo_rootx()+button.winfo_width(),win.winfo_rootx()+win.winfo_width())
                    self.assertEqual(win.cget('background'),palette['BG'])
                    report=next(w for w in widgets if isinstance(w,tk.Text))
                    self.assertEqual(report.cget('state'),'disabled');self.assertIn(t('contribution_explanation'),report.get('1.0','end'))
                    record.assert_not_called();win.destroy()
    def test_demo_has_no_identity_actions(self):
        with patch.dict(os.environ,{'BOTANEO_DEMO':'1'}):
            win=information.ouvrir_information(self.root,THEME_CLAIR);win.update()
            buttons=[w.cget('text') for w in descendants(win) if isinstance(w,tk.Button)]
            self.assertEqual(buttons,[t('close')]);win.destroy()
    def test_tracking_table_scrolls_without_changing_receipts(self):
        rows=[{'operation':'submit','label':'Fictional state','request_id':'fictional-'+'x'*90}]
        for lang in ('fr','en'):
            for palette in (THEME_CLAIR,THEME_SOMBRE):
                with self.subTest(lang=lang,theme=palette['BG']),utiliser_langue(lang),patch.object(tracking,'lister_demandes',return_value=rows):
                    win=tracking.ouvrir_suivi(self.root,palette);win.geometry('460x300');win.update();self.check_close(win)
                    tree=next(w for w in descendants(win) if isinstance(w,ttk.Treeview))
                    self.assertEqual(len(tree.get_children()),1)
                    tree.xview_moveto(1);win.update();self.assertGreater(tree.xview()[0],0)
                    self.assertEqual(tree.item(tree.get_children()[0],'values')[-1],rows[0]['request_id'])
                    win.destroy()

if __name__=='__main__':unittest.main()
