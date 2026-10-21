"""Exercise actual watering callbacks and SQLite on a disposable fictional database."""
import ast,sqlite3,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta
from contextlib import ExitStack
from unittest.mock import Mock,patch
import tkinter as tk
from tkinter import ttk
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import database,vue_historique as history
from services.analyse_arrosage import calculer_cycles_arrosage
from ui_palette import THEME_CLAIR,THEME_SOMBRE
from ui_data_events import notifier_donnees_modifiees
from i18n import utiliser_langue,traduire_courant as t
from test_alerts_consistency import functions as alert_functions

def descendants(w):
    for child in w.winfo_children():yield child;yield from descendants(child)
class Clock(datetime):
    instant=datetime(2026,10,19,10)
    @classmethod
    def now(cls,tz=None):return cls.instant.astimezone(tz) if tz else cls.instant
class WateringWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        directory=self.stack.enter_context(tempfile.TemporaryDirectory());path=Path(directory)/'fictional.db'
        self.stack.enter_context(patch.object(database,'_SCHEMA_INITIALISE',False))
        self.stack.enter_context(patch.object(database,'get_connection',side_effect=lambda:sqlite3.connect(path)))
        database.initialiser_schema();self.pid=database.ajouter_plante('Fictional plant','Fictional species')
        sensor=database.ajouter_capteur('Fictional Mi Flora','00:11:22:33:44:55',self.pid)
        for day in (1,5,10):database.enregistrer_arrosage_plante(self.pid,f'2026-10-{day:02}T10:00:00',quantite_ml=80,rappel_date='2026-10-11T10:00:00' if day==10 else None)
        with database.get_connection() as db:db.execute('INSERT INTO mesures (capteur_id,date_heure,temperature,humidite,luminosite,conductivite) VALUES (?,?,?,?,?,?)',(sensor,'2026-10-19T09:00:00',22,16,100,20))
        db.close()
        self.root=tk.Tk();self.root.geometry('460x300');self.addCleanup(self.root.destroy)
        tree=ast.parse((Path(__file__).resolve().parents[1]/'_app/interface.py').read_text(encoding='utf-8'))
        code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('ouvrir_arrosage_plante','code_etat_sante_depuis_libelle')],type_ignores=[])
        self.env={**THEME_CLAIR,'root':self.root,'tk':tk,'ttk':ttk,'t':t,'database':database,'datetime':Clock,'timedelta':timedelta,'messagebox':Mock(),'status_var':tk.StringVar(self.root),'formater_date':str,'analyser_apres_arrosage':Mock(return_value=None),'lancer_collecte_prioritaire_apres_arrosage':Mock(),'actualiser_interface':lambda:notifier_donnees_modifiees(self.root)}
        self.env['messagebox'].askyesno.return_value=True
        exec(compile(code,'real_watering_callback','exec'),self.env)
        Clock.instant=datetime(2026,10,19,10)
    def form(self,volume):
        self.env['ouvrir_arrosage_plante'](self.pid,'Fictional plant');self.root.update()
        window=next(w for w in self.root.winfo_children() if isinstance(w,tk.Toplevel) and w.title()==t('watering_title'))
        controls=list(descendants(window));entry=next(w for w in controls if isinstance(w,tk.Entry));entry.insert(0,volume)
        save=next(w for w in controls if isinstance(w,tk.Button) and w.cget('text')==t('save'))
        return window,controls,save
    def count(self):return len(database.get_arrosages_plante(self.pid))
    def test_confirmation_fraction_alert_and_history_refresh(self):
        with utiliser_langue('fr'),patch.object(history,'theme_actuel',return_value=history.THEME_CLAIR):
            view=history.ouvrir_historique(self.root,self.pid);self.root.update()
            alerts=alert_functions();alerts['database']=database
            self.assertTrue(any(a['niveau']=='danger' for a in alerts['construire_alertes']([(self.pid,'Fictional plant')])))
            window,controls,save=self.form('40')
            reminder=next(w for w in controls if isinstance(w,tk.Checkbutton) and w.cget('text')==t('schedule_reminder'));reminder.invoke()
            self.env['messagebox'].askyesno.return_value=False;save.invoke();self.assertEqual(self.count(),3)
            self.env['messagebox'].askyesno.return_value=True;save.invoke();self.root.update();self.assertEqual(self.count(),4)
            Clock.instant+=timedelta(minutes=15)
            window,controls,save=self.form('55');save.invoke();self.root.update()
            self.assertIn(t('watering_fraction_reminder_kept'),self.env['messagebox'].askyesno.call_args.args[1])
            waters=database.get_arrosages_plante(self.pid);self.assertEqual(len(waters),5)
            sessions=database.construire_sessions_arrosage(waters);self.assertEqual(len(sessions),4);self.assertEqual(sessions[-1]['quantite_totale_ml'],95)
            self.assertEqual(len(calculer_cycles_arrosage(database.get_mesures(self.pid,-1),waters)),4)
            self.assertFalse(any(a['niveau']=='danger' for a in alerts['construire_alertes']([(self.pid,'Fictional plant')])))
            texts=' '.join(str(w.cget('text')) for w in descendants(view) if isinstance(w,tk.Label))
            self.assertIn('5',texts)
    def test_saved_watering_survives_priority_failure_without_duplicate_retry(self):
        with utiliser_langue('fr'),patch.object(database,'enregistrer_collecte_prioritaire',side_effect=OSError('fictional failure')):
            window,_,save=self.form('40');save.invoke();self.root.update()
            self.assertEqual(self.count(),4);self.assertFalse(window.winfo_exists())
            self.assertIn(t('watering_saved_collect_unavailable'),self.env['status_var'].get())
            self.env['lancer_collecte_prioritaire_apres_arrosage'].assert_not_called()
    def test_invalid_values_do_not_reach_confirmation(self):
        for value in ('nan','inf','-5'):
            window,_,save=self.form(value);self.env['messagebox'].askyesno.reset_mock();save.invoke()
            self.assertEqual(self.count(),3);self.env['messagebox'].askyesno.assert_not_called();window.destroy()
    def test_footer_and_fields_accessible_in_both_languages_and_themes(self):
        for lang in ('fr','en'):
            for palette in (THEME_CLAIR,THEME_SOMBRE):
                with utiliser_langue(lang):
                    self.env.update(palette);window,_,save=self.form('40');window.geometry('460x500');self.root.update()
                    self.assertLessEqual(save.winfo_rooty()+save.winfo_height(),window.winfo_rooty()+window.winfo_height())
                    canvas=next(w for w in descendants(window) if isinstance(w,tk.Canvas))
                    self.assertLess(canvas.yview()[1],1);window.destroy()
if __name__=='__main__':unittest.main()
