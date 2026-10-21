from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

class DemoIsolationTests(unittest.TestCase):
    def test_demo_load_and_save_do_not_touch_existing_private_file(self):
        import home_assistant_ui as ui
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'private.json';path.write_text('FICTITIOUS PRIVATE SENTINEL')
            before=path.read_bytes()
            with patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch.object(ui,'read_private',side_effect=AssertionError('private')),patch.object(ui,'write_private',side_effect=AssertionError('write')),patch.object(ui,'lire_json',side_effect=AssertionError('file')):
                self.assertEqual(ui.load(path)['access_token'],'')
                with self.assertRaisesRegex(ValueError,'demo_disabled'):ui.save_config('','','',path)
            self.assertEqual(path.read_bytes(),before)
    def test_demo_commit_blocked_before_any_validation_or_file_access(self):
        import home_assistant_archive as archive
        with patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch.object(archive,'validate_config',side_effect=AssertionError('validation')),patch.object(archive,'_check_path',side_effect=AssertionError('file')):
            with self.assertRaisesRegex(ValueError,'demo_disabled'):archive.commit_history(None,None,None)
    def test_demo_settings_and_catchup_are_fictional_and_inert(self):
        import tkinter as tk
        from tkinter import ttk
        import home_assistant_ui as ui
        import home_assistant_catchup_ui as catchup
        def descendants(parent):
            for child in parent.winfo_children():
                yield child
                yield from descendants(child)
        root=tk.Tk();root.withdraw()
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with utiliser_langue(lang),patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch.object(ui,'load',side_effect=AssertionError('private config')),patch.object(ui,'save_config',side_effect=AssertionError('write')),patch.object(ui,'assess_mappings',side_effect=AssertionError('real inventory')),patch('home_assistant_view.plants',side_effect=AssertionError('real plants')),patch('home_assistant_archive.checkpoint',side_effect=AssertionError('real archive')),patch('home_assistant_catchup.plan_catchup',side_effect=AssertionError('real plan')):
                        win=ui.open_window(root,palette);win.geometry('620x440');win.update()
                        widgets=list(descendants(win));buttons={w.cget('text'):w for w in widgets if isinstance(w,tk.Button)}
                        table=next(w for w in widgets if isinstance(w,ttk.Treeview))
                        self.assertEqual(len(table.get_children()),4)
                        self.assertTrue(all(t('ha_authorization_demo') in table.item(row,'values') for row in table.get_children()))
                        for key in ('ha_save','ha_add','ha_edit','ha_remove','ha_catchup_title'):
                            self.assertEqual(buttons[t(key)].cget('state'),'disabled')
                        self.assertTrue(all(w.cget('state')=='disabled' for w in widgets if isinstance(w,tk.Entry)))
                        buttons[t('ha_save')].configure(state='normal');buttons[t('ha_save')].invoke()
                        win.destroy()
                        win=catchup.open_window(root,palette);win.update()
                        button=next(w for w in descendants(win) if isinstance(w,tk.Button) and w.cget('text')==t('ha_catchup_plan'))
                        self.assertEqual(button.cget('state'),'disabled')
                        button.configure(state='normal');button.invoke();win.update()
                        report=next(w for w in descendants(win) if isinstance(w,tk.Text))
                        self.assertEqual(report.get('1.0','end-1c'),t('ha_demo_settings'))
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
