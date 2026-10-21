import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from meteo_cache import CacheMeteo,recuperer_sources
from i18n import utiliser_langue,traduire_courant as t

class WeatherCacheStatusTests(unittest.TestCase):
    def test_old_cache_without_date_uses_unknown_not_never(self):
        for language in ('fr','en'):
            with self.subTest(language=language),utiliser_langue(language),tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'cache.json'
                path.write_text(json.dumps({'stations_privees':[{'nom':'Fictional'}]}))
                cache=CacheMeteo(path);text=cache.libelle()
                self.assertIn(t('weather_source_date_unknown'),text)
                self.assertNotIn('Jamais',text)
                self.assertNotIn('Never',text)
                self.assertIn(t('meteo_cache_text_52'),text)
    def test_failed_source_keeps_previous_data_and_retrieval_date(self):
        with tempfile.TemporaryDirectory() as directory:
            cache=CacheMeteo(Path(directory)/'cache.json')
            cache.appliquer({'privees':{'data':[{'nom':'Fictional'}],'date':'2026-10-18T08:00:00Z','error':None}})
            for invalid in (None,{'data':None,'error':None},{'data':'invalid','error':None}):
                cache.appliquer({'privees':invalid})
                self.assertEqual(cache.sources['privees']['date'],'2026-10-18T08:00:00Z')
                self.assertEqual(cache.sources['privees']['data'],[{'nom':'Fictional'}])
                self.assertTrue(cache.sources['privees']['error']);self.assertTrue(cache.sources['privees']['cache'])
    def test_wrong_cache_shape_and_invalid_dates_do_not_break_display(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cache.json';path.write_text('[]')
            cache=CacheMeteo(path);self.assertFalse(cache.sources['privees']['data'])
            path.write_text(json.dumps({'stations_privees':[{}],'dates':{'privees':123}}))
            cache=CacheMeteo(path);self.assertIn(t('weather_source_date_unknown'),cache.libelle())
    def test_empty_success_is_distinct_from_failed_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            cache=CacheMeteo(Path(directory)/'cache.json')
            api=SimpleNamespace(recuperer_netatmo=lambda:None,recuperer_stations_publiques=lambda:[])
            results=recuperer_sources(api);cache.appliquer(results)
            self.assertIsNotNone(results['privees']['error']);self.assertIsNone(results['publiques']['error'])
            self.assertIn(t('weather_source_no_stations'),cache.libelle())
            self.assertFalse(cache.sources['publiques']['error'])
