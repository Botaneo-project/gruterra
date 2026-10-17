import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
from contribution_donnees import valider_contribution_v2
import contribution_suivi as suivi


class DataContractTests(unittest.TestCase):
    def setUp(self):
        self.example=json.loads((Path(__file__).parent/'fixtures/contribution_donnees_v2.json').read_text(encoding='utf-8'))

    def test_fictional_example_and_fractional_waterings_remain_unchanged(self):
        original=copy.deepcopy(self.example)
        self.assertIs(valider_contribution_v2(self.example),self.example)
        self.assertEqual(self.example,original)
        self.assertEqual([e['water_volume_ml'] for e in self.example['events']],[40,55])

    def test_closed_fields_reject_private_information_and_unknown_versions(self):
        for field,value in [('private_seed_b64','secret'),('management_key','secret'),('email','user@example.invalid'),('schema_version',1),('schema_version',True)]:
            data=copy.deepcopy(self.example);data[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):valider_contribution_v2(data)
        data=copy.deepcopy(self.example);data['plants'][0]['name']='private name'
        with self.assertRaises(ValueError):valider_contribution_v2(data)

    def test_measurement_bounds_precision_time_and_duplicates(self):
        for field,value in [('moisture_pct',101),('moisture_pct',True),('moisture_pct',20.5),('temperature_c',20.123),('illuminance_lux',float('nan')),('illuminance_lux',10**1000),('elapsed_second',-1),('elapsed_hour',True),('elapsed_hour',876001),('plant_ref','p2')]:
            data=copy.deepcopy(self.example);data['measurements'][0][field]=value
            with self.subTest(field=field,value=str(value)[:30]),self.assertRaises(ValueError):valider_contribution_v2(data)
        data=copy.deepcopy(self.example);data['measurements'].append(copy.deepcopy(data['measurements'][0]))
        with self.assertRaises(ValueError):valider_contribution_v2(data)

    def test_event_unknown_volume_allowed_but_zero_or_null_rejected(self):
        data=copy.deepcopy(self.example);data['events'][0].pop('water_volume_ml')
        valider_contribution_v2(data)
        for volume in (0,-1,None,True,float('inf'),10**1000):
            data=copy.deepcopy(self.example);data['events'][0]['water_volume_ml']=volume
            with self.subTest(volume=str(volume)[:30]),self.assertRaises(ValueError):valider_contribution_v2(data)
        data=copy.deepcopy(self.example);data['events'].append(copy.deepcopy(data['events'][0]))
        valider_contribution_v2(data)  # Identical fractions are not automatically deduplicated.

    def test_invalid_content_creates_no_request_and_valid_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(suivi,'CONFIG_DIR',Path(folder)),patch.dict(os.environ,{'BOTANEO_DEMO':'0'}):
            data=copy.deepcopy(self.example);data['measurements'][0]['moisture_pct']=120
            with self.assertRaises(ValueError):suivi.preparer_demande('ed25519:'+'a'*64,'contribute',json.dumps(data).encode())
            self.assertFalse(suivi.chemin().exists())
            payload=json.dumps(self.example,ensure_ascii=False,indent=3).encode('utf-8')
            request=suivi.preparer_demande('ed25519:'+'a'*64,'contribute',payload)
            self.assertEqual(suivi.lire_demande(request)['payload'],payload)

    def test_empty_or_unused_plants_and_excessive_counts_rejected(self):
        cases=[dict(schema_version=2,plants=[],measurements=[],events=[])]
        data=copy.deepcopy(self.example);data['plants'].append({'plant_ref':'p2'});cases.append(data)
        data=copy.deepcopy(self.example);data['events']=[data['events'][0]]*2001;cases.append(data)
        for data in cases:
            with self.assertRaises(ValueError):valider_contribution_v2(data)
