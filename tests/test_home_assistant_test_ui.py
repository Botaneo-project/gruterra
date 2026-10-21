from pathlib import Path
import sys,time,tkinter as tk,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import home_assistant_test_ui as ui
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

def descendants(parent):
    for child in parent.winfo_children():
        yield child
        yield from descendants(child)

class TestDataUI(unittest.TestCase):
    def test_dst_and_invalid_range(self):
        start,end=ui.date_range('2026-10-25','2026-10-25')
        from datetime import datetime,timezone
        self.assertEqual((datetime.fromisoformat(end).astimezone(timezone.utc)-datetime.fromisoformat(start).astimezone(timezone.utc)).total_seconds(),25*3600)
        with self.assertRaises(ValueError):ui.date_range('2026-10-26','2026-10-25')
    def test_demo_never_reads_config_or_archive(self):
        root=tk.Tk();root.withdraw()
        try:
            with patch.dict('os.environ',{'BOTANEO_DEMO':'1'}),patch('home_assistant_ui.load',side_effect=AssertionError('private config')),patch('home_assistant_test_data.preview_test_purge',side_effect=AssertionError('archive')):
                win=ui.open_window(root,THEME_SOMBRE);win.update()
                buttons={w.cget('text'):w for w in descendants(win) if isinstance(w,tk.Button)}
                self.assertEqual(buttons[t('ha_test_preview')].cget('state'),'disabled')
                self.assertEqual(buttons[t('ha_test_remove')].cget('state'),'disabled')
                win.destroy()
        finally:root.destroy()
    def test_preview_confirmation_cancel_and_invalidation_small_window(self):
        root=tk.Tk();root.withdraw()
        row={'hardware_id':'zigbee:0011223344556677','model':'ZS-304Z','test_data':True}
        plan={'facts':3,'envelopes':4,'physical_id':row['hardware_id']}
        try:
            for lang in ('fr','en'):
                for palette in (THEME_CLAIR,THEME_SOMBRE):
                    with self.subTest(lang=lang,theme=palette['BG']),utiliser_langue(lang),patch('home_assistant_test_data.preview_test_purge',return_value=plan),patch('home_assistant_test_data.purge_test_data') as purge,patch('tkinter.messagebox.askyesno',return_value=False):
                        win=ui.open_window(root,palette,mappings=[row],archive_path='unused');win.geometry('560x390');win.update()
                        widgets=list(descendants(win));buttons={w.cget('text'):w for w in widgets if isinstance(w,tk.Button)}
                        buttons[t('ha_test_preview')].invoke()
                        deadline=time.monotonic()+3
                        while buttons[t('ha_test_remove')].cget('state')=='disabled' and time.monotonic()<deadline:
                            win.update();time.sleep(.01)
                        self.assertEqual(buttons[t('ha_test_remove')].cget('state'),'normal')
                        buttons[t('ha_test_remove')].invoke();purge.assert_not_called()
                        entry=next(w for w in widgets if type(w) is tk.Entry);entry.insert('end','x');win.update()
                        self.assertEqual(buttons[t('ha_test_remove')].cget('state'),'disabled')
                        for key in ('ha_test_remove','ha_close'):
                            b=buttons[t(key)]
                            self.assertLessEqual(b.winfo_rooty()+b.winfo_height(),win.winfo_rooty()+win.winfo_height())
                        win.destroy()
        finally:root.destroy()

if __name__=='__main__':unittest.main()
