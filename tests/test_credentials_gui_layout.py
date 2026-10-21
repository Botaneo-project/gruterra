import sys,tkinter as tk,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import arome_credentials_ui as arome
import netatmo_pi_credentials_ui as netatmo
from i18n import utiliser_langue,traduire_courant as t
from ui_palette import THEME_CLAIR,THEME_SOMBRE

def descendants(parent):
 for child in parent.winfo_children():
  yield child
  yield from descendants(child)

class CredentialsLayoutTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  try:cls.root=tk.Tk();cls.root.withdraw()
  except tk.TclError:raise unittest.SkipTest('Tk display unavailable')
 @classmethod
 def tearDownClass(cls):cls.root.destroy()
 def test_save_visible_and_fields_masked_at_large_text_scale(self):
  initial=float(self.root.tk.call('tk','scaling'))
  try:
   self.root.tk.call('tk','scaling',2.0)
   for module in (arome,netatmo):
    for language in ('fr','en'):
     for palette in (THEME_CLAIR,THEME_SOMBRE):
      with self.subTest(form=module.__name__,language=language,bg=palette['BG']),utiliser_langue(language),patch.object(module,'load',return_value={}):
       before=set(self.root.winfo_children());module.open_window(self.root,palette)
       window=next(w for w in self.root.winfo_children() if w not in before)
       try:
        window.geometry('560x440');window.update()
        widgets=list(descendants(window))
        save=next(w for w in widgets if isinstance(w,tk.Button) and w.cget('text')==t('netatmo_pi_save_credentials'))
        self.assertTrue(save.winfo_ismapped())
        self.assertLessEqual(save.winfo_rooty()+save.winfo_height(),window.winfo_rooty()+window.winfo_height())
        entries=[w for w in widgets if isinstance(w,tk.Entry)]
        self.assertTrue(any(w.cget('show')=='•' for w in entries))
        canvas=next(w for w in widgets if isinstance(w,tk.Canvas))
        canvas.yview_moveto(1);window.update()
        reveal=next(w for w in widgets if isinstance(w,tk.Checkbutton))
        self.assertLessEqual(reveal.winfo_rooty()+reveal.winfo_height(),canvas.winfo_rooty()+canvas.winfo_height())
        self.assertTrue(save.winfo_ismapped())
        for radio in (w for w in widgets if isinstance(w,tk.Radiobutton)):
         self.assertEqual(radio.cget('background'),palette['BG'])
       finally:window.destroy()
  finally:self.root.tk.call('tk','scaling',initial)
