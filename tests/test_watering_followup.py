from contextlib import closing
from datetime import datetime,timedelta
from pathlib import Path
import sqlite3,tempfile,unittest,sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import database,watering_schedule as schedule,watering_observations as observations


class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'fictional.db'
        mock=patch.object(database,'get_connection',side_effect=lambda:sqlite3.connect(self.path));mock.start();self.addCleanup(mock.stop)
        mock=patch.object(database,'_SCHEMA_INITIALISE',False);mock.start();self.addCleanup(mock.stop)
        database.initialiser_schema();self.plant=database.ajouter_plante('Fictional plant','fictional')
        self.time=datetime.now().replace(microsecond=0)
        self.water=database.enregistrer_arrosage_plante(self.plant,self.time.isoformat(),quantite_ml=40)
    def test_due_time_separate_request_survives_reload_and_no_early_claim(self):
        ids=[]
        for minute in (0,10):
            ids.append(database.enregistrer_collecte_prioritaire(self.plant,arrosage_id=self.water,date_creation=self.time.isoformat(),raison='post_arrosage' if minute==0 else 'post_arrosage_10min',date_prevue=(self.time+timedelta(minutes=minute)).isoformat()))
        self.assertNotEqual(*ids)
        self.assertFalse(schedule.claim(ids[1],self.time+timedelta(minutes=9,seconds=59)))
        self.assertTrue(schedule.claim(ids[0],self.time))
        database.marquer_collecte_prioritaire_tentee(ids[0],statut='reussie')
        self.assertIn((ids[1],self.plant),schedule.due_requests(self.time+timedelta(minutes=10)))
        self.assertTrue(schedule.claim(ids[1],self.time+timedelta(minutes=10)))
        self.assertFalse(schedule.claim(ids[1],self.time+timedelta(minutes=10)))
    def test_edit_runoff_keeps_watering_volume_time_and_count(self):
        before=database.get_arrosages_plante(self.plant)
        observations.save(self.plant,self.water,'light',3.5)
        observations.save(self.plant,self.water,'clear',4)
        self.assertEqual(observations.load(self.water)['first_drops_minutes'],4)
        self.assertEqual(database.get_arrosages_plante(self.plant),before)
        for drainage,minutes in [('none',3),('light',float('nan')),('clear',-1)]:
            with self.assertRaises(ValueError):observations.save(self.plant,self.water,drainage,minutes)
