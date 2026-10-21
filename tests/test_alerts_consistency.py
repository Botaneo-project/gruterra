"""Run the real alert functions without importing the application's startup."""
import ast
from datetime import datetime,timedelta,timezone
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_app'))
from services.alertes_temps import minutes_depuis,jours_avant,etat_prevision,trier_alertes
from botaneo_dates import vers_local_naif
from i18n import traduire_courant as t,utiliser_langue
from ui_palette import THEME_CLAIR,THEME_SOMBRE

NOW=datetime(2026,10,18,12)
class Clock(datetime):
    @classmethod
    def now(cls,tz=None):return NOW.astimezone(tz) if tz else NOW

def functions():
    # Importing interface.py would start Tk and open the real installation.
    # Compile the actual functions instead, with fictional dependencies below.
    tree=ast.parse((ROOT/'_app/interface.py').read_text(encoding='utf-8'))
    names={'age_mesure_minutes','anciennete','etat_fraicheur_mesure','delai_rappel_arrosage',
           'rappel_mail_texte','ajouter_alerte','alerte_humidite_basse','construire_alertes','afficher_tuile_alerte',
           'afficher_centre_alertes','afficher_prevision_2h','formater_prevision_valeur'}
    code=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names],type_ignores=[])
    db=SimpleNamespace(get_mesures_capteur=Mock(return_value=[]),get_rappel_arrosage_actif=Mock(return_value=None),get_dernier_arrosage=Mock(return_value=None))
    env={**THEME_CLAIR,'BG':THEME_CLAIR['BG'],'datetime':Clock,'timedelta':timedelta,'tk':tk,'t':t,
         'vers_local_naif':vers_local_naif,'minutes_depuis':lambda value,reference=None:minutes_depuis(value,reference or NOW),
         'jours_avant':lambda value,reference=None:jours_avant(value,reference or NOW),
         'etat_prevision':lambda data,reference=None:etat_prevision(data,reference or NOW),'trier_alertes':trier_alertes,
         'database':db,'capteurs_actifs_par_plante':lambda:{},'analyser_apres_arrosage':Mock(return_value=None),
         'plante_avec_rappel_email':lambda plant:False,'formater_date':lambda value:str(value),
         'lire_infos':lambda address:{},'obtenir_derniere_synchronisation_capteur':lambda sensor:None,
         'alertes_config':{'seuil_batterie':50},'prevision_2h_data':None,'prevision_2h_error':None,
         'creer_ligne_netatmo_compacte':Mock(),'ouvrir_apercu_email_alertes':Mock()}
    exec(compile(code,'interface_alert_functions','exec'),env)
    return env

class AlertConsistencyTests(unittest.TestCase):
    def soil_env(self, value=16, date=None, watering=None):
        env=functions()
        env['capteurs_actifs_par_plante']=lambda:{1:[(7,'Mi Flora fictif','fictional')]}
        env['database'].get_mesures_capteur.return_value=[(1,date or NOW.isoformat(),22,value,100,20,None,7)]
        env['database'].get_dernier_arrosage.return_value=watering
        return env

    def test_low_soil_without_recent_watering_is_visible_in_both_languages(self):
        for language in ('fr','en'):
            with utiliser_langue(language):
                env=self.soil_env()
                alerts=env['construire_alertes']([(1,'Crassula fictive')])
                soil=[a for a in alerts if a['titre']==t('alerts_low_soil_title').format(plant='Crassula fictive')]
                self.assertEqual(len(soil),1)
                self.assertEqual(soil[0]['niveau'],'attention')
                self.assertIn('Mi Flora fictif',soil[0]['detail'])
                self.assertIn('16',soil[0]['detail'])
                env['database'].get_mesures_capteur.assert_called_once_with(7,limite=1)

    def test_invalid_old_future_or_non_low_soil_cannot_trigger_watering_warning(self):
        for value in (None,True,float('nan'),float('inf'),-1,20,100,101):
            env=self.soil_env(value)
            self.assertIsNone(env['alerte_humidite_basse']((7,'sensor','addr'),None,NOW))
        for date in ((NOW-timedelta(hours=48)).isoformat(),(NOW+timedelta(minutes=1)).isoformat(),'invalid'):
            env=self.soil_env(16,date)
            self.assertIsNone(env['alerte_humidite_basse']((7,'sensor','addr'),None,NOW))
        env=self.soil_env(0)
        self.assertIsNotNone(env['alerte_humidite_basse']((7,'sensor','addr'),None,NOW))

    def test_new_watering_suppresses_previous_low_reading_until_new_sample(self):
        env=self.soil_env(16,(NOW-timedelta(hours=2)).isoformat())
        watering=(1,1,(NOW-timedelta(hours=1)).isoformat())
        self.assertIsNone(env['alerte_humidite_basse']((7,'sensor','addr'),watering,NOW))
        env['database'].get_mesures_capteur.return_value[0]=(2,NOW.isoformat(),22,16,100,20,None,7)
        self.assertIsNotNone(env['alerte_humidite_basse']((7,'sensor','addr'),watering,NOW))

    def test_aware_old_sensor_reading_still_produces_stale_alert(self):
        env=functions();env['capteurs_actifs_par_plante']=lambda:{1:[(1,'Fictional sensor','fictional',1,None,None,None,None,1)]}
        env['obtenir_derniere_synchronisation_capteur']=lambda sensor:(NOW.astimezone(timezone.utc)-timedelta(days=3)).isoformat()
        with utiliser_langue('fr'):
            alerts=env['construire_alertes']([(1,'Fictional plant')])
            self.assertTrue(any(a['niveau']=='attention' and a['titre']==t('interface_text_7514').format(v0='Fictional plant') for a in alerts))
    def test_future_or_missing_reading_is_not_recent(self):
        env=functions()
        with utiliser_langue('en'):
            self.assertIsNone(env['age_mesure_minutes']((NOW+timedelta(days=1)).isoformat()))
            self.assertIn(t('fresh_date_unknown'),env['etat_fraicheur_mesure']((NOW+timedelta(days=1)).isoformat()))
            self.assertEqual(env['etat_fraicheur_mesure'](None)[0],t('fresh_no_measure'))
    def test_reminder_near_three_calendar_days_is_not_two_day_warning(self):
        env=functions();reminder=[None]*12;reminder[9]='2026-10-21T08:00:00'
        env['database'].get_rappel_arrosage_actif.return_value=reminder
        alerts=env['construire_alertes']([(1,'Fictional plant')])
        self.assertFalse(any(a['niveau'] in ('attention','danger') for a in alerts))
        reminder[9]='2026-10-20T23:00:00'
        self.assertTrue(any(a['niveau']=='attention' for a in env['construire_alertes']([(1,'Fictional plant')])))
    def test_expired_or_undated_weather_is_information_not_upcoming_gust_alarm(self):
        for date in (None,(NOW-timedelta(hours=3)).isoformat()):
            env=functions();env['prevision_2h_data']={'date':date,'pluie_2h':10,'rafale':90}
            alerts=env['construire_alertes']([])
            self.assertEqual(len(alerts),1);self.assertEqual(alerts[0]['niveau'],'info')
        env['prevision_2h_data']['date']=NOW.isoformat()
        self.assertTrue(any(a['niveau']=='attention' for a in env['construire_alertes']([])))
    def test_priority_alerts_precede_the_first_six_informational_plants(self):
        env=functions();plants=[(i,'Fictional '+str(i)) for i in range(8)]
        reminder=[None]*12;reminder[9]='2026-10-17T08:00:00'
        env['database'].get_rappel_arrosage_actif.side_effect=lambda plant:reminder if plant==7 else None
        alerts=env['construire_alertes'](plants)
        self.assertEqual(alerts[0]['niveau'],'danger');self.assertIn('Fictional 7',alerts[0]['titre'])
    def test_failed_reminder_read_does_not_imply_successful_check(self):
        env=functions();env['database'].get_rappel_arrosage_actif.side_effect=OSError('fictional unavailable')
        with utiliser_langue('fr'):
            alerts=env['construire_alertes']([(1,'Fictional plant')])
            self.assertTrue(any(a['titre']==t('alerts_reminder_unavailable').format(plant='Fictional plant') for a in alerts))
    def test_unreadable_sensor_list_does_not_become_no_sensor_or_hide_reminder(self):
        env=functions();env['capteurs_actifs_par_plante']=lambda:None
        reminder=[None]*12;reminder[9]='2026-10-17T08:00:00'
        env['database'].get_rappel_arrosage_actif.return_value=reminder
        with utiliser_langue('fr'):
            alerts=env['construire_alertes']([(1,'Fictional plant')])
            self.assertEqual(alerts[0]['niveau'],'danger')
            self.assertTrue(any(a['titre']==t('alerts_sensor_list_unavailable') for a in alerts))
            self.assertFalse(any(a['titre']==t('interface_text_7465').format(v0='Fictional plant') for a in alerts))

    def test_malformed_sensor_metadata_cannot_crash_alert_loading(self):
        import capteur_infos
        with patch.object(capteur_infos,'lire_json',return_value=[]):
            self.assertEqual(capteur_infos.lire_infos('fictional'),{})

    def test_actual_new_watering_removes_the_old_due_alert(self):
        import database
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fictional.db'
            with patch.object(database,'get_connection',side_effect=lambda:sqlite3.connect(path)):
                database.initialiser_schema();plant=database.ajouter_plante('Fictional plant','Fictitious')
                database.enregistrer_arrosage_plante(plant,'2026-10-01T10:00:00',quantite_ml=40,rappel_date='2026-10-02T10:00:00')
                env=functions();env['database']=database
                self.assertTrue(any(a['niveau']=='danger' for a in env['construire_alertes']([(plant,'Fictional plant')])))
                database.enregistrer_arrosage_plante(plant,'2026-10-18T10:00:00',quantite_ml=40,rappel_date='2026-10-25T10:00:00')
                self.assertFalse(any(a['niveau']=='danger' for a in env['construire_alertes']([(plant,'Fictional plant')])))
    def test_no_future_forecast_slots_cannot_fall_back_to_midnight_weather(self):
        import previsions_meteo
        payload={'hourly':{'time':['2026-10-17T00:00','2026-10-17T01:00'],'rain':[8,8],'wind_gusts_10m':[80,80]}}
        with patch.object(previsions_meteo,'datetime',Clock),patch.object(previsions_meteo,'parametres_prevision',return_value=(0,0)),patch.object(previsions_meteo,'urlopen',return_value=io.BytesIO(json.dumps(payload).encode())):
            with self.assertRaises(RuntimeError):previsions_meteo.recuperer_prevision_2h()

class ForecastMissingValuesTests(unittest.TestCase):
    def forecast(self, hourly):
        import previsions_meteo
        # Source hours have the requested Paris timezone, independently of host.
        paris=NOW.astimezone().astimezone(__import__('zoneinfo').ZoneInfo('Europe/Paris'))
        hourly={'time':[(paris+timedelta(hours=1)).replace(tzinfo=None).isoformat(),
                        (paris+timedelta(hours=2)).replace(tzinfo=None).isoformat()],**hourly}
        with patch.object(previsions_meteo,'datetime',Clock),patch.object(previsions_meteo,'parametres_prevision',return_value=(0,0)),patch.object(previsions_meteo,'urlopen',return_value=io.BytesIO(json.dumps({'hourly':hourly}).encode())):
            return previsions_meteo.recuperer_prevision_2h()
    def test_missing_or_partial_rain_is_not_a_zero_total(self):
        for values in ({},{'rain':[None,None]},{'rain':[1,None]}, {'rain':[float('nan'),0]}):
            with self.subTest(values=values):
                result=self.forecast(values)
                self.assertIsNone(result['pluie_2h']);self.assertIsNone(result['intensite_max'])
    def test_two_valid_zero_values_are_a_real_zero_forecast(self):
        result=self.forecast({'rain':[0,0],'precipitation':[0,0]})
        self.assertEqual(result['pluie_2h'],0);self.assertEqual(result['intensite_max'],0)


class AlertLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:cls.root=tk.Tk();cls.root.withdraw()
        except tk.TclError:raise unittest.SkipTest('Tk display unavailable')
    @classmethod
    def tearDownClass(cls):cls.root.destroy()
    def test_level_and_long_details_wrap_in_both_languages_and_themes(self):
        for language in ('fr','en'):
            for palette in (THEME_CLAIR,THEME_SOMBRE):
                with utiliser_langue(language):
                    env=functions();env.update(palette)
                    window=tk.Toplevel(self.root);window.geometry('600x420');frame=tk.Frame(window);frame.pack(fill='x')
                    try:
                        alerts=[];env['ajouter_alerte'](alerts,'danger','Fictional long alert title '*4,'Long contextual detail '*12)
                        env['afficher_tuile_alerte'](frame,alerts[0]);window.update()
                        labels=[w for tile in frame.winfo_children() for w in tile.winfo_children() if isinstance(w,tk.Label)]
                        self.assertTrue(labels[0].cget('text').startswith(t('alerts_level_danger')))
                        for label in labels:
                            self.assertLessEqual(label.winfo_rootx()+label.winfo_width(),window.winfo_rootx()+window.winfo_width())
                            self.assertGreater(int(label.cget('wraplength')),0)
                    finally:window.destroy()
    def test_expired_forecast_card_does_not_render_old_values_as_upcoming(self):
        env=functions();env['prevision_2h_data']={'date':(NOW-timedelta(days=1)).isoformat(),'rafale':90}
        window=tk.Toplevel(self.root)
        try:
            env['afficher_prevision_2h'](window);window.update()
            env['creer_ligne_netatmo_compacte'].assert_not_called()
        finally:window.destroy()

    def test_more_than_six_alerts_can_be_expanded_and_stay_expanded_after_refresh(self):
        env=functions();items=[]
        for index in range(8):env['ajouter_alerte'](items,'info','Fictional alert '+str(index),'Detail')
        env['construire_alertes']=lambda plants:items
        window=tk.Toplevel(self.root);parent=tk.Frame(window);parent.pack(fill='both',expand=True)
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        try:
            env['afficher_centre_alertes'](parent,[]);window.update()
            labels=lambda:[w.cget('text') for w in descendants(parent) if isinstance(w,tk.Label) and 'Fictional alert' in str(w.cget('text'))]
            self.assertEqual(len(labels()),6)
            button=next(w for w in descendants(parent) if isinstance(w,tk.Button) and w.cget('text')==t('alerts_show_all').format(count=2))
            button.invoke();window.update();self.assertEqual(len(labels()),8)
            for child in parent.winfo_children():child.destroy()
            env['afficher_centre_alertes'](parent,[]);window.update()
            self.assertEqual(len(labels()),8)
            button=next(w for w in descendants(parent) if isinstance(w,tk.Button) and w.cget('text')==t('alerts_show_less'))
            button.invoke();window.update();self.assertEqual(len(labels()),6)
        finally:window.destroy()
