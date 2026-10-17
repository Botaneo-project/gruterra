import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from capteurs.netatmo import extraire_mesures_publiques
from meteo_synthese import choisir_mesure


class WeatherSummaryTests(unittest.TestCase):
    def choose(self,key,private=(),public=()):
        return choisir_mesure(key,private,public,lambda s:s.get('nom','Public'),lambda v,u:f'{v:g}{u}')

    def test_public_rain_zero_and_per_metric_dates_are_kept(self):
        raw={'measures':{'rain':{'rain_60min':0,'rain_24h':0,'rain_live':0,'rain_timeutc':1791712800},
                         'temperature':{'type':['temperature','humidity'],'res':{'1791712700':[14,75]}}}}
        result=extraire_mesures_publiques(raw)
        self.assertEqual(result['pluie_24h'],0)
        self.assertNotEqual(result['dates_mesures']['temperature'],result['dates_mesures']['pluie_24h'])
        chosen=self.choose('pluie_24h',public=[{'mesures':{'brut':raw},'distance_m':100}])
        self.assertEqual(chosen['etat'],'ok');self.assertEqual(chosen['texte'],'0')
        self.assertTrue(chosen['date'])

    def test_personal_outdoor_module_used_instead_of_indoor_temperature(self):
        private=[{'nom':'Home','distance_m':0,'mesures':{'temperature':24,'pression':1010},'modules':[
            {'type':'NAModule4','nom':'Inside','mesures':{'temperature':25}},
            {'type':'NAModule1','nom':'Outside','mesures':{'temperature':12,'date_mesure':'11/10/2026 10:00'}}]}]
        result=self.choose('temperature',private)
        self.assertEqual(result['texte'],'12');self.assertIn('Outside',result['source'])
        self.assertEqual(self.choose('pression',private)['texte'],'1010')
        private[0]['modules']=[]
        self.assertEqual(self.choose('temperature',private)['etat'],'absent')

    def test_favorite_complements_personal_station_before_nearest(self):
        stations=[{'nom':'Favorite','favorite':True,'distance_m':2000,'mesures':{'temperature':18}},
                  {'nom':'Near','distance_m':30,'mesures':{'temperature':14}},
                  {'nom':'Closest','distance_m':10,'mesures':{'pluie_24h':2}}]
        result=self.choose('temperature',public=stations)
        self.assertEqual(result['texte'],'18');self.assertIn('Favorite',result['source'])
        self.assertEqual(self.choose('pluie_24h',public=stations)['texte'],'2')

    def test_missing_rain_has_no_false_source_and_no_zero(self):
        result=self.choose('pluie_24h',private=[{'mesures':{'temperature':22},'modules':[]}],public=[{'mesures':{'temperature':14}}])
        self.assertEqual(result['etat'],'absent');self.assertIsNone(result['source'])
        self.assertIn('0 mm',result['explication'])

    def test_public_latest_timestamp_is_selected_not_dictionary_order(self):
        raw={'measures':{'module':{'type':['temperature'],'res':{'1791712800':[15],'1791712700':[14]}}}}
        self.assertEqual(extraire_mesures_publiques(raw)['temperature'],15)

    def test_personal_rain_and_wind_modules_are_available_and_invalid_values_skipped(self):
        private=[{'nom':'Home','modules':[{'type':'NAModule3','mesures':{'pluie_24h':0}},
                                        {'type':'NAModule2','mesures':{'vent':6}}]}]
        self.assertEqual(self.choose('pluie_24h',private)['texte'],'0')
        self.assertEqual(self.choose('vent',private)['texte'],'6')
        self.assertEqual(self.choose('temperature',public=[{'mesures':{'temperature':float('nan')}}])['etat'],'absent')


    def test_personal_time_utc_is_extracted_and_old_cache_repaired(self):
        from capteurs.netatmo import extraire_mesures
        raw={'Temperature':14,'Humidity':70,'time_utc':1791712800}
        self.assertTrue(extraire_mesures({'dashboard_data':raw})['date_mesure'])
        station={'nom':'Home','modules':[{'type':'NAModule1','mesures':{'temperature':14,'brut':raw,'date_mesure':None}}]}
        self.assertTrue(self.choose('temperature',[station])['date'])
