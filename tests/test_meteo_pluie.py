import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from meteo_pluie import enregistrer,derniere_pluie
from meteo_synthese import choisir_mesure

class RainTests(unittest.TestCase):
    def test_dedup_missing_zero_error_and_positive(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'rain.sqlite3'
            def result(value,date='11/10/2026 11:00',error=None):
                return {'publiques':{'error':error,'date':'2026-10-11T09:00:01+00:00','data':[{'id':'fictive','nom':'Test','mesures':{'pluie_1h':value,'date_mesure':date}}]}}
            self.assertEqual(enregistrer(path,result(0)),1)
            self.assertIsNone(derniere_pluie(path))
            self.assertEqual(enregistrer(path,result(0)),0)
            self.assertEqual(enregistrer(path,result(2,'11/10/2026 12:00')),1)
            self.assertEqual(derniere_pluie(path)[1],2)
            self.assertEqual(enregistrer(path,result(3,None)),0)
            self.assertEqual(enregistrer(path,result(3,error='failed')),0)
            self.assertEqual(enregistrer(path,result(-1)),0)
    def test_personal_priority_then_favorite_then_nearest(self):
        own=[{'nom':'Own','distance_m':5000,'modules':[{'type':'NAModule3','mesures':{'pluie_1h':0}}]}]
        public=[{'nom':'Fav','favorite':True,'distance_m':2000,'mesures':{'pluie_1h':3}},{'nom':'Near','distance_m':10,'mesures':{'pluie_1h':1}}]
        choose=lambda private,pub:choisir_mesure('pluie_1h',private,pub,lambda s:s['nom'],lambda v,u:str(v))
        self.assertEqual(choose(own,public)['valeur'],0)
        self.assertEqual(choose([],public)['valeur'],3)
        self.assertEqual(choose([],public[1:])['valeur'],1)

if __name__=='__main__':unittest.main()
