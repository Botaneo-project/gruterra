import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from meteo_cache import CacheMeteo

class FallbackTests(unittest.TestCase):
 def test_consultation_preserves_history_and_refreshes_cache(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'cache.json';history=path.with_name('netatmo_pluie.sqlite3');history.write_bytes(b'unchanged history')
   state=CacheMeteo(path)
   results={'publiques':{'error':None,'data':[{'nom':'Fictive','mesures':{'pluie_1h':2}}],'date':'2026-10-11T10:00:00Z'}}
   with patch('meteo_pluie.enregistrer') as archive:
    self.assertTrue(state.appliquer(results));archive.assert_not_called()
   self.assertTrue(path.exists());self.assertEqual(history.read_bytes(),b'unchanged history')
   self.assertEqual(state.sources['publiques']['data'][0]['mesures']['pluie_1h'],2)
 def test_fresh_install_does_not_create_history(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'cache.json';state=CacheMeteo(path)
   self.assertTrue(state.appliquer({'publiques':{'error':None,'data':[],'date':'2026-10-11T10:00:00Z'}}))
   self.assertFalse(path.with_name('netatmo_pluie.sqlite3').exists())

if __name__=='__main__':unittest.main()
