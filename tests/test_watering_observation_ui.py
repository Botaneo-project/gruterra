import sys,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import tkinter as tk
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import database,watering_observations as observations
from ui_palette import THEME_CLAIR,THEME_SOMBRE
from i18n import utiliser_langue,traduire_courant as t


def descendants(w):
    for child in w.winfo_children():yield child;yield from descendants(child)


class ObservationUITests(unittest.TestCase):
    def test_edit_afterwards_in_both_languages_themes_and_small_window(self):
        with ExitStack() as stack:
            folder=stack.enter_context(tempfile.TemporaryDirectory());path=Path(folder)/'fictional.db'
            stack.enter_context(patch.object(database,'get_connection',side_effect=lambda:sqlite3.connect(path)))
            stack.enter_context(patch.object(database,'_SCHEMA_INITIALISE',False))
            database.initialiser_schema();plant=database.ajouter_plante('Fictional','fictional')
            watering=database.enregistrer_arrosage_plante(plant,'2026-10-20T10:00:00',quantite_ml=40)
            before=database.get_arrosages_plante(plant)
            root=tk.Tk();root.withdraw()
            try:
                for lang in ('fr','en'):
                    with utiliser_langue(lang):
                        for palette in (THEME_CLAIR,THEME_SOMBRE):
                            win=observations.open_editor(root,plant,palette);win.geometry('440x300');root.update()
                            widgets=list(descendants(win));combos=[w for w in widgets if isinstance(w,ttk.Combobox)]
                            combos[1].current(2)
                            entry=next(w for w in widgets if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox));entry.delete(0,'end');entry.insert(0,'3,5')
                            save=next(w for w in widgets if isinstance(w,ttk.Button) and w.cget('text')==t('save'))
                            self.assertLessEqual(save.winfo_rooty()+save.winfo_height(),win.winfo_rooty()+win.winfo_height())
                            save.invoke();root.update()
                            self.assertEqual(observations.load(watering)['first_drops_minutes'],3.5)
                            self.assertEqual(database.get_arrosages_plante(plant),before)
                            win.destroy()
            finally:root.destroy()
