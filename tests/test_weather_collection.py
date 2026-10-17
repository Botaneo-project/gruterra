import copy
import json
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from contextlib import closing
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'_app'),str(ROOT/'raspberry')]
import weather_collect as c
import weather_backup as b
import weather_backup_pc as remote_backup
import weather_outbox as outbox
import weather_store as store

class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);(self.base/'data').mkdir();(self.base/'config').mkdir()
        self.stamp=1760000000
        self.public={'body':[{'_id':'station-test','measures':{'module-test':{'rain_60min':0,'rain_24h':None,'rain_timeutc':self.stamp}}}]}
        self.personal={'body':{'devices':[{'_id':'personal-test','dashboard_data':{'Pressure':Decimal('1013.12'),'Temperature':22,'time_utc':self.stamp},'modules':[{'_id':'outside-test','type':'NAModule1','dashboard_data':{'Temperature':Decimal('-1.25'),'Humidity':80,'time_utc':self.stamp}}]}]}}
        c.atomic(self.base/'config/collector.json',{'device_id':'pi-fictif'})
        c.atomic(self.base/'config/weather.json',{'enabled':True,'public_station_ids':['station-test'],'public_bounds':dict(lat_ne=49,lat_sw=48,lon_ne=3,lon_sw=2)})
        self.oauth=self.base/'config/weather-oauth.json'
        c.atomic(self.oauth,dict(independent_authorization=True,client_id='test-only',client_secret='test-only',refresh_token='test-refresh',access_token='test-access',expires_at=int(time.time())+3600))

    def fake(self,url,token=None,form=None):
        if url.endswith('/oauth2/token'):return dict(access_token='rotated-test-access',refresh_token='rotated-test-refresh',expires_in=10800,scope='read_station')
        return self.personal if 'getstationsdata' in url else self.public

    def test_zero_null_and_source_dates(self):
        rows,missing=c.public_rows(self.public,['station-test'],'2026-10-12T12:00:00Z')
        self.assertEqual(missing,[]);self.assertEqual(len(rows),2)
        by={r['observation']['api_field']:r['observation'] for r in rows}
        self.assertEqual(by['rain_60min']['value'],'0');self.assertIsNone(by['rain_24h']['value'])
        self.assertEqual(by['rain_60min']['source_time'],c.utc(self.stamp))
        self.assertEqual(by['rain_60min']['unit'],'mm');self.assertEqual(by['rain_24h']['period']['kind'],'unknown')
        self.assertNotIn('rain_live',by)

    def test_personal_outdoor_only_and_decimal_precision(self):
        rows=c.personal_rows(self.personal,'2026-10-12T12:00:00Z')
        values={(r['observation']['module_id'],r['observation']['api_field']):r['observation']['value'] for r in rows}
        self.assertNotIn(('personal-test','Temperature'),values)
        self.assertEqual(values[('outside-test','Temperature')],'-1.25')
        self.assertEqual(values[('personal-test','Pressure')],'1013.12')

    def test_cycle_replay_backup_restore_import(self):
        self.assertEqual(c.cycle(self.base,self.fake)['status'],'ok')
        first=outbox.export_batch(self.base/'data/weather.sqlite3','pi-fictif')
        self.assertEqual(c.cycle(self.base,self.fake)['sources']['public']['added'],0)
        backup=b.backup(self.base);self.assertEqual(backup['status'],'verified')
        meta=b.manifest(self.base);saved=self.base/'backups/weather'/meta['name']
        remote_backup.verify(saved,meta)
        restored=self.base/'restored.sqlite3';shutil.copy2(saved,restored)
        batch=outbox.export_batch(restored,'pi-fictif');self.assertEqual(batch,first)
        counts,ack=store.import_batch(self.base/'pc.sqlite3',batch,'pi-fictif')
        self.assertEqual(counts['added'],5)
        self.assertEqual(outbox.acknowledge(restored,'pi-fictif',ack)['confirmed'],5)
        self.assertEqual(outbox.export_batch(restored,'pi-fictif')['pending'],0)
        self.assertEqual(outbox.export_batch(self.base/'data/weather.sqlite3','pi-fictif')['pending'],5)

    def test_network_failure_keeps_data(self):
        c.cycle(self.base,self.fake)
        def fail(*args,**kwargs):raise c.Failure('network_unavailable')
        result=c.cycle(self.base,fail)
        self.assertEqual(result['status'],'partial')
        self.assertEqual(outbox.export_batch(self.base/'data/weather.sqlite3','pi-fictif')['pending'],5)

    def test_refresh_rotates_and_persists(self):
        config=json.loads(self.oauth.read_text());config['expires_at']=0;c.atomic(self.oauth,config)
        result=c.cycle(self.base,self.fake)
        self.assertEqual(result['status'],'ok');self.assertEqual(result['requests'],3)
        self.assertEqual(json.loads(self.oauth.read_text())['refresh_token'],'rotated-test-refresh')
        self.assertNotIn('rotated-test',json.dumps(result))

    def test_401_refresh_once(self):
        client=c.Client(self.oauth,self.fake)
        def request(url,token=None,form=None):
            if token=='test-access':raise c.Failure('http_401')
            return self.fake(url,token,form)
        client.request=request
        self.assertEqual(client.get('getstationsdata'),self.personal)
        self.assertEqual(client.calls,3)

    def test_rate_limit_persists_backoff(self):
        def fail(*args,**kwargs):raise c.Failure('rate_limited',7200)
        result=c.cycle(self.base,fail)
        self.assertGreater(result['retry_at'],time.time()+7100)
        def forbidden(*args,**kwargs):raise AssertionError('network called during backoff')
        self.assertEqual(c.cycle(self.base,forbidden)['status'],'backoff')

    def test_no_shared_oauth_or_disabled_collection(self):
        config=json.loads(self.oauth.read_text());config['independent_authorization']=False;c.atomic(self.oauth,config)
        with self.assertRaises(c.Failure):c.Client(self.oauth,self.fake)
        settings=json.loads((self.base/'config/weather.json').read_text());settings['enabled']=False;c.atomic(self.base/'config/weather.json',settings)
        self.assertEqual(c.cycle(self.base,self.fake)['code'],'disabled')

    def test_invalid_grant_no_secret_logged(self):
        config=json.loads(self.oauth.read_text());config['expires_at']=0;c.atomic(self.oauth,config)
        def fail(*args,**kwargs):raise c.Failure('http_400')
        result=c.cycle(self.base,fail)
        self.assertEqual(result['sources']['personal']['code'],'authorization_required')
        self.assertNotIn('test-refresh',json.dumps(result))

    def test_missing_station_and_unknown_date(self):
        rows,missing=c.public_rows(self.public,['another-station'],'2026-10-12T12:00:00Z')
        self.assertEqual(rows,[]);self.assertEqual(missing,['another-station'])
        row=c.row('netatmo_public','s','m','rain_60min',0,None,'2026-10-12T12:00:00Z')
        self.assertTrue(row['observation_id'].startswith('wu1_'));self.assertIsNone(row['observation']['source_time'])

    def test_http_errors_expiry_and_retry_after_date(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        from io import BytesIO
        from email.utils import formatdate
        headers={'Retry-After':formatdate(time.time()+7200,usegmt=True)}
        with patch.object(c,'urlopen',side_effect=HTTPError('https://example.invalid',429,'limit',headers,BytesIO(b''))):
            with self.assertRaises(c.Failure) as error:c.http('https://example.invalid')
            self.assertGreater(error.exception.retry_after,7100)
        with patch.object(c,'urlopen',side_effect=HTTPError('https://example.invalid',403,'expired',{},BytesIO(b'{"error":{"message":"Access token expired"}}'))):
            with self.assertRaises(c.Failure) as error:c.http('https://example.invalid')
            self.assertEqual(error.exception.code,'http_401')

    def test_invalid_bounds_never_call_network(self):
        settings=json.loads((self.base/'config/weather.json').read_text());settings['public_bounds']['lat_ne']=None;c.atomic(self.base/'config/weather.json',settings)
        def forbidden(*args,**kwargs):raise AssertionError('network must not run')
        result=c.cycle(self.base,forbidden)
        self.assertEqual(result['code'],'invalid_settings')

if __name__=='__main__':unittest.main()
