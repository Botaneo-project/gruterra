"""Small-window catch-up UI checks, fictional configuration and no network."""
from pathlib import Path
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_app'))
import home_assistant_catchup_ui as ui
from i18n import utiliser_langue, traduire_courant as t
from ui_palette import THEME_CLAIR, THEME_SOMBRE

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class CatchupLayoutTests(unittest.TestCase):
    def test_settings_remain_accessible_without_reading_or_saving_credentials(self):
        import home_assistant_ui
        root=tk.Tk();root.withdraw()
        original=root.tk.call('tk','scaling')
        try:
            root.tk.call('tk','scaling',2.0)
            for language in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with self.subTest(language=language,theme=palette['BG']), utiliser_langue(language), patch.object(home_assistant_ui,'load',return_value={'entities':[]}), patch.object(home_assistant_ui,'save_config',side_effect=ValueError('invalid_url')) as save:
                        win=home_assistant_ui.open_window(root,palette);win.geometry('620x440');win.update()
                        widgets=list(descendants(win))
                        buttons={w.cget('text'):w for w in widgets if isinstance(w,tk.Button)}
                        self.assertTrue(any(w.cget('show') for w in widgets if isinstance(w,tk.Entry)))
                        buttons[t('ha_save')].invoke();win.update();save.assert_called_once()
                        self.assertTrue(any(w.cget('textvariable') and w.getvar(w.cget('textvariable'))==t('ha_error_url') for w in widgets if isinstance(w,tk.Label)))
                        for key in ('ha_save','ha_close'):
                            button=buttons[t(key)]
                            self.assertGreater(button.winfo_height(),10)
                            self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),win.winfo_rooty()+win.winfo_height())
                        canvas=next(w for w in widgets if isinstance(w,tk.Canvas))
                        canvas.yview_moveto(1);win.update()
                        self.assertGreater(canvas.yview()[0],0)
                        self.assertEqual(canvas.cget('background'),palette['BG'])
                        win.destroy()
        finally:
            root.tk.call('tk','scaling',original);root.destroy()

    def test_long_report_scrolls_and_copies_with_visible_actions(self):
        root=tk.Tk();root.withdraw()
        original=root.tk.call('tk','scaling')
        try:
            root.tk.call('tk','scaling',2.0)
            for language in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with self.subTest(language=language,theme=palette['BG']), utiliser_langue(language):
                        with patch('home_assistant_ui.load',return_value={}), patch('home_assistant_archive.checkpoint',return_value=None), patch('home_assistant_catchup.plan_catchup',side_effect=RuntimeError('fictional')):
                            win=ui.open_window(root,palette);win.geometry('620x420');win.update()
                            widgets=list(descendants(win))
                            buttons={w.cget('text'):w for w in widgets if isinstance(w,tk.Button)}
                            report=next(w for w in widgets if isinstance(w,tk.Text))
                            # Invoke the actual planning failure path, not a synthetic label.
                            buttons[t('ha_catchup_plan')].invoke();win.update()
                            self.assertEqual(report.get('1.0','end-1c'),t('ha_catchup_plan_failed'))
                            report.configure(state='normal')
                            report.insert('end','\n'+('Long fictional report é → 🌱\n'*80))
                            report.configure(state='disabled');report.yview_moveto(1);win.update()
                            self.assertGreater(report.yview()[0],0)
                            report.tag_add('sel','1.0','end-1c');report.event_generate('<<Copy>>');win.update()
                            self.assertIn('Long fictional report',win.clipboard_get())
                            self.assertEqual(report.cget('state'),'disabled')
                            self.assertEqual(report.cget('background'),palette['BG'])
                            for key in ('ha_close','ha_catchup_confirm'):
                                button=buttons[t(key)]
                                self.assertGreater(button.winfo_height(),10)
                                self.assertLessEqual(button.winfo_rooty()+button.winfo_height(),win.winfo_rooty()+win.winfo_height())
                            win.destroy()
        finally:
            root.tk.call('tk','scaling',original);root.destroy()

if __name__=='__main__': unittest.main()
