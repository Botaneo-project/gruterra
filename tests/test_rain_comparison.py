import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import pluie_meteofrance as m

class ComparisonTests(unittest.TestCase):
 def test_selected_cache_zero_and_no_network(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'cache.json'
   path.write_text(json.dumps({'stations_publiques':[{'id':'other','nom':'Other','mesures':{'pluie_1h':99}},{'id':'fictional-selected','nom':'Selected','favorite':True,'distance_m':1259,'mesures':{'pluie_1h':0,'pluie_24h':2,'date_mesure':'12/10/2026 18:45'}}]}),encoding='utf-8')
   original=path.read_bytes()
   with patch.object(m.requests.Session,'get',side_effect=AssertionError('network forbidden')):
    rows=m.netatmo_snapshot(path)
   self.assertEqual([row['mm'] for row in rows],[0,2]);self.assertEqual([row['period_hours'] for row in rows],[1,24]);self.assertEqual(rows[0]['date'],'12/10/2026 18:45');self.assertEqual(path.read_bytes(),original)
 def test_missing_selected_station_no_substitution(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'cache.json';path.write_text(json.dumps({'stations_publiques':[{'id':'other','mesures':{'pluie_1h':3}}]}),encoding='utf-8')
   self.assertEqual(m.netatmo_snapshot(path),[])


 def test_nearest_favorite_ignores_nonfavorite_and_invalid_distances(self):
  stations=[
   {'id':'near-unselected','distance_m':1,'mesures':{'pluie_1h':99}},
   {'id':'unknown-distance','favorite':True,'distance_m':float('nan'),'mesures':{'pluie_1h':8}},
   {'id':'far','favorite':True,'distance_m':2000,'mesures':{'pluie_1h':4}},
   {'id':'near','favorite':True,'distance_m':500,'mesures':{'pluie_1h':0}},
  ]
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'cache.json'
   path.write_text(json.dumps({'stations_publiques':stations}),encoding='utf-8')
   rows=m.netatmo_snapshot(path)
   self.assertEqual([row['mm'] for row in rows],[0])
   self.assertEqual(rows[0]['distance_m'],500)

 def test_explicit_station_overrides_favorite_and_missing_does_not_fallback(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'cache.json'
   path.write_text(json.dumps({'stations_publiques':[
    {'id':'favorite','favorite':True,'distance_m':1,'mesures':{'pluie_1h':99}},
    {'id':'explicit','mesures':{'pluie_1h':2}},
   ]}),encoding='utf-8')
   self.assertEqual([row['mm'] for row in m.netatmo_snapshot(path,station_id='explicit')],[2])
   self.assertEqual(m.netatmo_snapshot(path,station_id='missing'),[])

if __name__=='__main__':unittest.main()
