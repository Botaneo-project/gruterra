from pathlib import Path
import sys
import sqlite3
import tempfile
import copy
from contextlib import closing
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import home_assistant_ui as ui

class SyncActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.plants=Path(self.tmp.name)/'plants.db';self.path=Path(self.tmp.name)/'private.json'
        self.path.write_bytes(b'FICTIONAL EXISTING PRIVATE FILE')
        with closing(sqlite3.connect(self.plants)) as db,db:
            db.execute('CREATE TABLE capteurs(adresse_ble TEXT)')
            db.execute('INSERT INTO capteurs VALUES (?)',('AA:BB:CC:DD:EE:FF',))
        self.mapping={'entity_id':'sensor.fictional','device_id':'fictional','model':'fictional',
                      'metric':'soil_moisture','hardware_id':'zigbee:0011223344556677','hardware_confirmed':True}
        self.config={'schema_version':1,'enabled':False,'instance_id':'existing-fictional-identity','entities':[]}
    def save(self,entities=None,**kwargs):
        return ui.save_config(kwargs.pop('url','https://example.invalid'),kwargs.pop('token','fictional-token'),
                              [self.mapping] if entities is None else entities,self.path,
                              plant_db_path=kwargs.pop('plant_db_path',self.plants),**kwargs)
    def test_blocked_activation_preserves_existing_private_file_and_never_connects(self):
        cases=[('sync_connection_required',{'url':''}),('sync_connection_required',{'token':''}),
               ('sync_entities_required',{'entities':[]}),
               ('sync_identity_pending',{'entities':[{**self.mapping,'hardware_confirmed':False}]}),
               ('sync_duplicate',{'entities':[self.mapping,{**self.mapping,'entity_id':'sensor.alias'}]}),
               ('sync_already_ble',{'entities':[{**self.mapping,'hardware_id':'ble:aa-bb-cc-dd-ee-ff'}]}),
               ('sync_registry_unavailable',{'plant_db_path':self.plants.parent/'missing.db'})]
        before=self.path.read_bytes()
        with patch.object(ui,'load',side_effect=lambda path:copy.deepcopy(self.config)),patch.object(ui,'write_private') as write,patch('requests.Session',side_effect=AssertionError('network')):
            for code,kwargs in cases:
                with self.subTest(code=code):
                    with self.assertRaisesRegex(ValueError,'^'+code+'$'):self.save(sync_on_request=True,**kwargs)
                    write.assert_not_called();self.assertEqual(self.path.read_bytes(),before)
    def test_valid_selection_enables_sync_without_replacing_identity_or_connecting(self):
        with patch.object(ui,'load',side_effect=lambda path:copy.deepcopy(self.config)),patch.object(ui,'write_private') as write,patch('requests.Session',side_effect=AssertionError('network')):
            result=self.save(sync_on_request=True)
        self.assertTrue(result['sync_on_request']);self.assertFalse(result['enabled'])
        self.assertEqual(result['instance_id'],'existing-fictional-identity')
        write.assert_called_once()
    def test_draft_still_saves_with_sync_unchecked_even_if_registry_unavailable(self):
        with patch.object(ui,'load',side_effect=lambda path:copy.deepcopy(self.config)),patch.object(ui,'write_private') as write,patch.object(ui,'assess_mappings',side_effect=AssertionError('registry')):
            result=self.save(entities=[],url='',token='',sync_on_request=False)
        self.assertFalse(result['sync_on_request']);write.assert_called_once()
    def test_existing_sync_cannot_silently_accept_unconfirmed_mapping(self):
        self.config['sync_on_request']=True
        with patch.object(ui,'load',side_effect=lambda path:copy.deepcopy(self.config)),patch.object(ui,'write_private') as write:
            with self.assertRaisesRegex(ValueError,'sync_identity_pending'):
                self.save(entities=[{**self.mapping,'hardware_confirmed':False}])
            write.assert_not_called()

if __name__=='__main__':unittest.main()
