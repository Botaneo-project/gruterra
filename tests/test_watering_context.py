"""Fictional session scenarios; no actual plant database or network."""
from datetime import datetime,timedelta
from pathlib import Path
import copy,json,sys,unittest
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from services.suivi_arrosage_alertes import observer_session,message,charger_contextes,dernier_signal_sante,observer_cycles
from database import construire_sessions_arrosage
from i18n import utiliser_langue

START=datetime(2026,10,20,20)
def row(minutes,soil=18,ec=53,sensor=7,raw=None):
    return (minutes,(START+timedelta(minutes=minutes)).isoformat(),22,soil,100,ec,raw,sensor)
def session():
    a=(1,1,START.isoformat(),30,'normal',None,None,None,'fictional water',None,None,None)
    b=(2,1,(START+timedelta(minutes=10)).isoformat(),40,'normal',None,None,None,'fictional water',None,None,None)
    return construire_sessions_arrosage([b,a])[0]

class WateringContextTests(unittest.TestCase):
    def observe(self,rows,**kwargs):return observer_session(session(),rows,7,START+timedelta(hours=24),**kwargs)
    def test_fractional_example_is_one_session_raw_events_preserved(self):
        s=session();original=copy.deepcopy(s);rows=[row(-5,16,21),row(5,17,35),row(20,18,53)]
        r=observer_session(s,rows,7,START+timedelta(hours=1))
        self.assertEqual(s,original);self.assertEqual(r['volume'],70);self.assertEqual(r['fractions'],2)
        self.assertEqual(r['soil_before'][1],16);self.assertEqual(r['soil_after'][1],18)
        self.assertEqual(r['ec_before'][1],21);self.assertEqual(r['ec_after'][1],53)
        self.assertEqual(r['state'],'response');self.assertEqual(r['level'],'attention')
        self.assertEqual(r['confidence'],'limited');self.assertIsNone(r['drying_rate_day'])
        for language in ('fr','en'):
            with utiliser_langue(language):
                detail=message(r,'Fictional Mi Flora')
                for value in ('70 ml','16','18','21','53','20','Fictional Mi Flora'):self.assertIn(value,detail)
    def test_no_increase_and_conductivity_only_are_not_failure(self):
        self.assertEqual(self.observe([row(-1,16,21),row(20,16,21)])['state'],'no_response')
        self.assertEqual(self.observe([row(-1,16,21),row(20,16,55)])['state'],'ec_only')
    def test_missing_pre_reading_cannot_establish_response(self):
        r=self.observe([row(20)]);self.assertEqual(r['confidence'],'limited');self.assertEqual(r['state'],'no_response')
        self.assertIsNone(self.observe([row(-1500,16),row(20)])['soil_before'])
    def test_no_recent_post_reading_is_waiting(self):
        r=self.observe([row(-1,16)]);self.assertEqual(r['state'],'waiting')
        r=observer_session(session(),[row(20)],7,START+timedelta(days=3));self.assertEqual(r['state'],'waiting')
    def test_duplicates_and_other_sensor_do_not_create_temporal_evidence(self):
        rows=[row(-1,16),row(20),row(20),row(20,sensor=8)]
        r=self.observe(rows);self.assertEqual(len(r['soil_points']),1);self.assertIsNone(r['drying_rate_day'])
    def test_same_time_conflicts_not_averaged_and_ec_stays_independent(self):
        r=self.observe([row(-1,16,21),row(20,18,53),row(20,22,53)])
        self.assertIsNone(r['soil_after']);self.assertEqual(r['ec_after'][1],53)
        self.assertEqual(r['conflicts'],1);self.assertEqual(r['state'],'waiting')
    def test_flagged_manual_tests_are_excluded_without_mutating_rows(self):
        rows=[row(-1,16),row(20,18),row(30,95,raw=json.dumps({'manual_test':True}))];original=copy.deepcopy(rows)
        r=self.observe(rows);self.assertEqual(r['peak'][1],18);self.assertEqual(r['excluded'],1);self.assertEqual(rows,original)
    def test_future_nan_bool_and_invalid_values_cannot_establish_response(self):
        for value in (True,float('nan'),float('inf'),-1,101,None):
            self.assertEqual(self.observe([row(-1,16),row(20,value)])['state'],'waiting')
        self.assertEqual(self.observe([row(-1,16),row(2000)])['state'],'waiting')
        self.assertEqual(self.observe([row(-1,0),row(20,0)])['soil_after'][1],0)
    def test_rate_requires_temporal_coverage_and_gaps_are_not_interpolated(self):
        r=self.observe([row(-1,16),row(20,30),row(80,27),row(140,24),row(400,17)])
        self.assertEqual(r['state'],'falling');self.assertIsNotNone(r['drying_rate_day'])
        r=self.observe([row(-1,16),row(20,30),row(80,27),row(140,24),row(1300,17)])
        self.assertIsNone(r['drying_rate_day']);self.assertEqual(r['confidence'],'limited')
        r=self.observe([row(-1,16)]+[row(i,30-i) for i in range(11,20)])
        self.assertIsNone(r['drying_rate_day'])
    def test_return_to_initial_is_a_crossing_bracket_not_an_exact_time(self):
        r=self.observe([row(-1,16),row(20,18),row(100,17),row(200,16)])
        self.assertEqual(r['return_bracket'],(START+timedelta(minutes=100),START+timedelta(minutes=200)))
        self.assertIsNone(self.observe([row(-1,16),row(20,18),row(1000,16)])['return_bracket'])
    def test_later_session_bounds_earlier_cycle(self):
        r=self.observe([row(-1,16),row(20,18),row(200,95)],next_start=START+timedelta(minutes=100))
        self.assertEqual(r['peak'][1],18)
        second=copy.deepcopy(session());second['date_debut']=START+timedelta(minutes=100);second['date_fin']=START+timedelta(minutes=110)
        cycles=observer_cycles([second,session()],[row(-1,16),row(20,18),row(200,95)],7,START+timedelta(hours=24))
        self.assertEqual(len(cycles),2);self.assertEqual(cycles[0]['peak'][1],18);self.assertEqual(cycles[1]['peak'][1],95)
    def test_old_or_future_session_has_no_active_alert(self):
        db=SimpleNamespace(get_derniere_session_arrosage=Mock(return_value=session()),get_mesures_capteur=Mock())
        for now in (START-timedelta(hours=1),START+timedelta(days=3)):
            self.assertEqual(charger_contextes(db,1,[(7,'fictional')],now),{})
        db.get_mesures_capteur.assert_not_called()
    def test_user_health_signal_survives_watering_until_new_assessment(self):
        entry=(1,1,START.isoformat(),'evaluation_sante','fictional','etat_sante=degrade signes=feuilles_souples','demo')
        db=SimpleNamespace(get_journal_plante=Mock(return_value=[entry]))
        self.assertIsNotNone(dernier_signal_sante(db,1,START+timedelta(days=1)))
        newer=(2,1,(START+timedelta(hours=1)).isoformat(),'evaluation_sante','fictional','etat_sante=bon_etat','demo')
        db.get_journal_plante.return_value=[entry,newer]
        self.assertIsNone(dernier_signal_sante(db,1,START+timedelta(days=1)))
        db.get_journal_plante.return_value=[(*entry[:5],'etat_sante=inconnu signes=soft_leaf',entry[6])]
        self.assertIsNotNone(dernier_signal_sante(db,1,START+timedelta(days=1)))
        db.get_journal_plante.return_value=[(*entry[:5],'etat_sante=inconnu signes=new_growth',entry[6])]
        self.assertIsNone(dernier_signal_sante(db,1,START+timedelta(days=1)))

    def test_existing_demo_displays_recent_fractional_followup(self):
        import tempfile,sqlite3
        from unittest.mock import patch
        import creer_base_demo as demo
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(demo,'DEMO_DIR',root),patch.object(demo,'DEMO_DB',root/'demo.db'),patch.object(demo,'SOURCE_DB',root/'absent.db'):
                path=demo.creer_base_demo()
                with closing(sqlite3.connect(path)) as db:
                    events=db.execute('SELECT id,plante_id,date_heure,quantite_ml FROM arrosages WHERE plante_id=1').fetchall()
                    rows=db.execute('SELECT id,date_heure,temperature,humidite,luminosite,conductivite,donnees_brutes,capteur_id FROM mesures WHERE capteur_id=1').fetchall()
                s=construire_sessions_arrosage(events)[-1]
                r=observer_session(s,rows,1,datetime.now())
                self.assertEqual(r['fractions'],2);self.assertEqual(r['volume'],95)
                self.assertLess(r['days'],2);self.assertGreater(r['amplitude'],0)
                self.assertIn(r['state'],('response','falling'))

class AlertIntegrationTests(unittest.TestCase):
    def test_context_replaces_threshold_but_does_not_hide_critical_alert(self):
        from test_alerts_consistency import functions,NOW
        env=functions();db=env['database'];start=NOW-timedelta(hours=2)
        s=session();s['date_debut']=start;s['date_fin']=start+timedelta(minutes=10)
        db.get_derniere_session_arrosage=Mock(return_value=s)
        db.get_mesures_capteur.return_value=[(1,(start-timedelta(minutes=5)).isoformat(),22,16,100,21,None,7),(2,(start+timedelta(minutes=20)).isoformat(),22,18,100,53,None,7)]
        env['capteurs_actifs_par_plante']=lambda:{1:[(7,'Fictional Mi Flora','fictional')]}
        env['analyser_apres_arrosage'].return_value={'niveau':'danger','titre':'Existing critical alert','detail':'Keep critical alert'}
        env['lire_infos']=lambda address:{'batterie':1}
        for language in ('fr','en'):
            with utiliser_langue(language):
                alerts=env['construire_alertes']([(1,'Fictional Crassula')])
                self.assertTrue(any('70 ml' in a['detail'] for a in alerts))
                self.assertTrue(any('Keep critical alert'==a['detail'] for a in alerts))
                self.assertGreaterEqual(sum(a['niveau']=='danger' for a in alerts),2)
                from i18n import traduire_courant as t
                self.assertFalse(any(a['titre']==t('alerts_low_soil_title').format(plant='Fictional Crassula') for a in alerts))
