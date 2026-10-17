import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from unittest.mock import patch
import meteo_nappes as m

class NappesTests(unittest.TestCase):
    def test_normalisation_dates_units_and_invalid_data(self):
        rows=m.normaliser([{'date_mesure':'2026-10-10','niveau_nappe_eau':69.05,'profondeur_nappe':2.7,'qualification':'Correcte','statut':'Donnée contrôlée niveau 1'},
                          {'date_mesure':'2026-10-09','niveau_nappe_eau':68},
                          {'date_mesure':'bad','niveau_nappe_eau':4},
                          {'date_mesure':'2026-10-10','niveau_nappe_eau':float('nan')},
                          {'date_mesure':'2026-10-10','niveau_nappe_eau':True}])
        self.assertEqual(len(rows),2);self.assertEqual(rows[-1]['niveau'],69.05)
        self.assertEqual(rows[-1]['statut'],'Donnée contrôlée niveau 1');self.assertEqual(rows[0]['statut'],'')
        self.assertEqual(rows[-1]['profondeur'],2.7);self.assertIsNone(rows[0]['profondeur'])
    def test_department_filter_recent_first_and_limit(self):
        with patch.object(m,'requete',return_value={'data':[{'code_bss':'old','date_fin_mesure':'1971-01-01'},{'code_bss':'new','date_fin_mesure':'2026-10-10'}],'next':'page2'}) as fetch:
            stations,limited=m.rechercher('59');self.assertEqual(stations[0]['code_bss'],'new');self.assertTrue(limited)
            self.assertEqual(fetch.call_args_list[0].args,('stations',{'code_departement':'59','size':500,'page':1}))
        with patch.object(m,'requete') as fetch:
            with self.assertRaises(ValueError):m.rechercher('not a department')
            fetch.assert_not_called()
    def test_closed_endpoints_and_history_query(self):
        with self.assertRaises(ValueError):m.requete('../elsewhere',{})
        with patch.object(m,'requete',return_value={'data':[]}) as fetch:
            self.assertEqual(m.historique('TEST/F'),[])
            fetch.assert_called_once_with('chroniques',{'code_bss':'TEST/F','size':100,'sort':'desc'})


    def test_postal_code_and_department_validation(self):
        self.assertEqual(m.normaliser_departement('92 380'), '92')
        self.assertEqual(m.normaliser_departement('92'), '92')
        self.assertEqual(m.normaliser_departement('38100'), '38')
        self.assertEqual(m.normaliser_departement('97100'), '971')
        self.assertEqual(m.normaliser_departement('2a'), '2A')
        for value in ('380','00','96','20000','hello'):
            with self.assertRaises(ValueError):m.normaliser_departement(value)

    def test_safe_error_classification(self):
        from urllib.error import HTTPError,URLError
        import ssl
        error=HTTPError('https://test',503,'secret',{},None)
        try:self.assertIn('503',m.erreur_lisible(error))
        finally:error.close()
        for error in (URLError('private-proxy-secret'), ValueError('private-response-secret')):
            self.assertNotIn('secret',m.erreur_lisible(error))
        self.assertNotEqual(m.erreur_lisible(URLError(ssl.SSLCertVerificationError())),m.erreur_lisible(URLError('offline')))

    def test_recent_filter_and_pagination(self):
        from datetime import date
        stations=[{'code_bss':'old','date_fin_mesure':'1992-10-01'}, {'code_bss':'new','date_fin_mesure':'2026-10-10'}, {'code_bss':'unknown'}]
        self.assertEqual([r['code_bss'] for r in m.trier_stations(stations,aujourd_hui=date(2026,10,11))],['new'])
        self.assertEqual(len(m.trier_stations(stations,True)),3)
        with patch.object(m,'requete',side_effect=[{'data':stations[:1],'next':'page2'},{'data':stations[1:],'next':None}]) as fetch:
            rows,limited=m.rechercher('92')
            self.assertEqual(rows[0]['code_bss'],'new');self.assertFalse(limited)
            self.assertEqual(fetch.call_args_list[1].args[1]['page'],2)
