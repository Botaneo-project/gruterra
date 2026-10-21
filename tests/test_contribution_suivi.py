import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import contribution_suivi as module


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for context in (patch.object(module,'CONFIG_DIR',Path(self.temp.name)),patch.dict(os.environ,{'BOTANEO_DEMO':'0'})):
            context.start();self.addCleanup(context.stop)
        self.identity='ed25519:'+'a'*64
        self.payload=b'{"schema_version":2,"plants":[{"plant_ref":"p1"}],"measurements":[],"events":[{"plant_ref":"p1","elapsed_hour":0,"elapsed_second":0,"event_type":"watering"}]}'
        self.contribution_id='10000000-0000-4000-8000-000000000001'

    def prepare(self,identity=None):
        return module.preparer_demande(identity or self.identity,'contribute',self.payload)

    def receipt(self,request_id,contribution_id=None,retention=None):
        return {'protocol_version':2,'mode':'private_test','status':'accepted','contributor_id':self.identity,
                'request_id':request_id,'contribution_id':contribution_id or self.contribution_id,
                'schema_version':2,'payload_sha256':hashlib.sha256(self.payload).hexdigest(),
                'received_at':'2026-10-10T12:00:00Z','withdrawal_endpoint':'https://api.gruterra.fr/v2/withdrawals',
                'policy_version':'private-test-only','retention_until':retention}

    def accept(self,retention=None):
        request=self.prepare();module.marquer_en_attente(request)
        receipt=self.receipt(request,retention=retention)
        module.enregistrer_recu(request,receipt,201)
        return request,receipt

    def withdraw(self,scope='contribution'):
        body={'scope':scope}
        if scope=='contribution':body['contribution_id']=self.contribution_id
        request=module.preparer_demande(self.identity,'withdraw',json.dumps(body).encode())
        module.marquer_en_attente(request)
        receipt={'protocol_version':2,'mode':'private_test','status':'withdrawn','contributor_id':self.identity,
                 'request_id':request,'scope':scope,'withdrawn_count':1,'processed_at':'2026-10-10T13:00:00Z'}
        return request,receipt

    def test_restart_and_retry_keep_exact_payload_and_receipt(self):
        request=self.prepare()
        self.assertEqual(module.etat_local(request)['status'],'prepared')
        module.marquer_en_attente(request)
        self.assertEqual(module.etat_local(request)['status'],'pending')
        module.marquer_en_attente(request)
        self.assertEqual(module.lire_demande(request)['payload'],self.payload)
        receipt=self.receipt(request)
        module.enregistrer_recu(request,receipt,201)
        module.enregistrer_recu(request,receipt,200)
        state=module.etat_local(request)
        self.assertEqual(state['status'],'received')
        self.assertEqual(state['receipt'],receipt)
        self.assertTrue(state['test_only'])
        self.assertFalse(state['server_deletion_verified'])

    def test_invalid_receipt_never_becomes_success_or_new_request(self):
        for field,value in [('payload_sha256','bad'),('contributor_id','ed25519:'+'b'*64),
                            ('request_id',self.contribution_id),('withdrawal_endpoint','https://evil.invalid/remove'),
                            ('schema_version',True),('mode','public')]:
            with self.subTest(field=field):
                request=self.prepare();module.marquer_en_attente(request)
                receipt=self.receipt(request);receipt[field]=value
                with self.assertRaises(ValueError):module.enregistrer_recu(request,receipt,201)
                self.assertEqual(module.etat_local(request)['status'],'check')
                self.assertEqual(module.lire_demande(request)['payload'],self.payload)
                # Terminer cette demande pour permettre la suivante.
                module.enregistrer_recu(request,self.receipt(request,contribution_id=request),201)

    def test_deadline_is_not_verified_deletion_and_null_is_not_infinite(self):
        request,_=self.accept(retention='2026-10-11T12:00:00Z')
        before=datetime(2026,10,11,11,59,tzinfo=timezone.utc)
        after=datetime(2026,10,11,12,0,tzinfo=timezone.utc)
        self.assertEqual(module.etat_local(request,before)['status'],'received')
        state=module.etat_local(request,after)
        self.assertEqual(state['status'],'deadline_reached')
        self.assertFalse(state['server_deletion_verified'])
        self.assertEqual(state['receipt']['status'],'accepted')
        second=self.prepare();module.marquer_en_attente(second)
        module.enregistrer_recu(second,self.receipt(second,contribution_id=second),201)
        self.assertEqual(module.etat_local(second,after)['status'],'received')
        self.assertTrue(module.etat_local(second,after)['test_only'])

    def test_confirmed_withdrawal_preserves_original_receipt(self):
        contribution,accepted=self.accept()
        withdrawal,receipt=self.withdraw()
        self.assertEqual(module.etat_local(withdrawal)['status'],'withdrawal_pending')
        self.assertEqual(module.etat_local(contribution)['status'],'received')
        module.enregistrer_recu(withdrawal,receipt,201)
        self.assertEqual(module.etat_local(withdrawal)['status'],'withdrawal_confirmed')
        self.assertEqual(module.etat_local(contribution)['status'],'withdrawn')
        self.assertEqual(module.etat_local(contribution)['receipt'],accepted)

    def test_global_withdrawal_replay_does_not_cover_later_contributions(self):
        first,_=self.accept();withdrawal,receipt=self.withdraw('all')
        module.enregistrer_recu(withdrawal,receipt,201)
        later=self.prepare();module.marquer_en_attente(later)
        module.enregistrer_recu(later,self.receipt(later,contribution_id=later),201)
        module.enregistrer_recu(withdrawal,receipt,200)
        self.assertEqual(module.etat_local(first)['status'],'withdrawn')
        self.assertEqual(module.etat_local(later)['status'],'received')
        with self.assertRaises(ValueError):module.marquer_en_attente(withdrawal)

    def test_serial_operations_per_identity_but_not_between_identities(self):
        first=self.prepare();module.marquer_en_attente(first)
        second=self.prepare()
        with self.assertRaises(ValueError):module.marquer_en_attente(second)
        other=self.prepare(identity='ed25519:'+'b'*64)
        module.marquer_en_attente(other)
        self.assertEqual(module.etat_local(other)['status'],'pending')

    def test_receipt_cannot_be_rewritten_or_contribution_id_reused(self):
        first,receipt=self.accept()
        changed=dict(receipt,received_at='2026-10-10T12:01:00Z')
        with self.assertRaises(ValueError):module.enregistrer_recu(first,changed,200)
        self.assertEqual(module.etat_local(first)['receipt'],receipt)
        second=self.prepare();module.marquer_en_attente(second)
        with self.assertRaises(ValueError):module.enregistrer_recu(second,self.receipt(second),201)
        self.assertEqual(module.etat_local(second)['status'],'check')

    def test_demo_and_bad_payload_do_not_create_history(self):
        with patch.dict(os.environ,{'BOTANEO_DEMO':'1'}):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(module.chemin().exists())
        for payload in (b'{"scope":"all","scope":"all"}',b'{"scope":"all","extra":true}',b'{"scope":"all","bad":NaN}'):
            with self.assertRaises(ValueError):module.preparer_demande(self.identity,'withdraw',payload)
        self.assertFalse(module.chemin().exists())


    def test_withdrawal_preparation_does_not_claim_a_request_was_sent(self):
        request=module.preparer_demande(self.identity,'withdraw',b'{"scope":"all"}')
        self.assertEqual(module.etat_local(request)['status'],'prepared')
        module.marquer_en_attente(request)
        self.assertEqual(module.etat_local(request)['status'],'withdrawal_pending')

    def test_global_withdrawal_does_not_affect_another_identity(self):
        first,_=self.accept()
        other_identity='ed25519:'+'b'*64
        other=self.prepare(other_identity)
        module.marquer_en_attente(other)
        other_receipt=dict(self.receipt(other,contribution_id=other),contributor_id=other_identity)
        module.enregistrer_recu(other,other_receipt,201)
        withdrawal,receipt=self.withdraw('all')
        module.enregistrer_recu(withdrawal,receipt,201)
        self.assertEqual(module.etat_local(first)['status'],'withdrawn')
        self.assertEqual(module.etat_local(other)['status'],'received')

    def test_concurrent_attempts_for_one_identity_have_only_one_winner(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        requests=[self.prepare(),self.prepare()]
        barrier=Barrier(2)
        def attempt(request):
            barrier.wait(timeout=5)
            try:
                module.marquer_en_attente(request)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(attempt,requests))
        self.assertEqual(sorted(results),[False,True])
        self.assertEqual(sorted(module.etat_local(r)['status'] for r in requests),['pending','prepared'])

    def test_full_backup_preserves_receipts_and_shared_export_excludes_tracking(self):
        import zipfile
        from sauvegarde_utilisateur import creer_sauvegarde_utilisateur
        contribution,accepted=self.accept()
        withdrawal,receipt=self.withdraw()
        module.enregistrer_recu(withdrawal,receipt,201)
        folder=Path(self.temp.name)
        # Give the backup its normal installation layout, without using real data.
        install=folder/'installation'
        private=install/'_config'
        private.mkdir(parents=True)
        import shutil
        shutil.copy2(module.chemin(),private/'contribution_suivi.sqlite3')
        import sqlite3
        (install/'_app').mkdir(exist_ok=True)
        with sqlite3.connect(install/'_app/plantes.db') as backup_fixture:
            backup_fixture.execute('CREATE TABLE fictive (id INTEGER)')
        backup_fixture.close()
        full=creer_sauvegarde_utilisateur(install,'complete',folder/'full')
        shared=creer_sauvegarde_utilisateur(install,'donnees',folder/'shared')
        restored=folder/'restored'
        restored.mkdir()
        with zipfile.ZipFile(full) as archive:
            name='_config/contribution_suivi.sqlite3'
            self.assertIn(name,archive.namelist())
            (restored/'contribution_suivi.sqlite3').write_bytes(archive.read(name))
        with zipfile.ZipFile(shared) as archive:
            self.assertNotIn(name,archive.namelist())
        with patch.object(module,'CONFIG_DIR',restored):
            self.assertEqual(module.etat_local(contribution)['status'],'withdrawn')
            self.assertEqual(module.etat_local(contribution)['receipt'],accepted)
            self.assertEqual(module.etat_local(withdrawal)['receipt'],receipt)
            self.assertEqual(module.lire_demande(contribution)['payload'],self.payload)


    def test_lifecycle_profile_requires_explicit_selection_and_exact_duration(self):
        for retention in (None,'2026-10-10T12:00:59Z','2026-10-10T12:01:01Z'):
            request=module.preparer_demande(self.identity,'contribute',self.payload,profil_test='lifecycle-test-60s')
            module.marquer_en_attente(request)
            receipt=dict(self.receipt(request,contribution_id=request,retention=retention),policy_version='lifecycle-test-60s')
            with self.assertRaises(ValueError):module.enregistrer_recu(request,receipt,201)
            self.assertEqual(module.etat_local(request)['status'],'check')
            valid=dict(receipt,retention_until='2026-10-10T12:01:00Z')
            module.enregistrer_recu(request,valid,201)
            module.enregistrer_recu(request,valid,200)
            self.assertEqual(module.etat_local(request)['receipt'],valid)
        historic=self.prepare();module.marquer_en_attente(historic)
        receipt=dict(self.receipt(historic,contribution_id=historic,retention='2026-10-10T12:01:00Z'),policy_version='lifecycle-test-60s')
        with self.assertRaises(ValueError):module.enregistrer_recu(historic,receipt,201)
        with self.assertRaises(ValueError):module.preparer_demande(self.identity,'contribute',self.payload,profil_test='public')

    def test_server_terminal_response_preserves_receipt_and_disallows_reactivation(self):
        request,receipt=self.accept()
        module.enregistrer_fin_parcours(request,{'error':'contribution_expired'},410)
        module.enregistrer_fin_parcours(request,{'error':'contribution_expired'},410)
        state=module.etat_local(request)
        self.assertEqual(state['status'],'server_expired')
        self.assertFalse(state['server_deletion_verified'])
        self.assertEqual(state['receipt'],receipt)
        self.assertEqual(module.lire_demande(request)['payload'],self.payload)
        with self.assertRaises(ValueError):module.marquer_en_attente(request)
        with self.assertRaises(ValueError):module.enregistrer_recu(request,receipt,200)
        with self.assertRaises(ValueError):module.enregistrer_fin_parcours(request,{'error':'contribution_withdrawn'},410)
        other=self.prepare();module.marquer_en_attente(other)
        module.enregistrer_fin_parcours(other,{'error':'contribution_withdrawn'},410)
        self.assertEqual(module.etat_local(other)['status'],'server_withdrawn')

    def test_ambiguous_errors_and_unsent_requests_do_not_become_terminal(self):
        request=self.prepare()
        with self.assertRaises(ValueError):module.enregistrer_fin_parcours(request,{'error':'contribution_expired'},410)
        module.marquer_en_attente(request)
        for response,code in [({'error':'contribution_unavailable'},410),({'error':'contribution_expired'},503),({'error':'contribution_expired','extra':1},410)]:
            with self.assertRaises(ValueError):module.enregistrer_fin_parcours(request,response,code)
            self.assertEqual(module.etat_local(request)['status'],'pending')

    def test_legacy_history_migration_preserves_request_and_exact_bytes(self):
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(module.chemin())) as conn:
            conn.execute('CREATE TABLE requests (request_id TEXT PRIMARY KEY,contributor_id TEXT NOT NULL,operation TEXT NOT NULL,payload BLOB NOT NULL,payload_sha256 TEXT NOT NULL,state TEXT NOT NULL,receipt TEXT)')
            request='20000000-0000-4000-8000-000000000001'
            conn.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,NULL)',(request,self.identity,'contribute',self.payload,hashlib.sha256(self.payload).hexdigest(),'pending'))
            conn.commit()
        row=module.lire_demande(request)
        self.assertEqual(row['test_profile'],'private-test-only')
        self.assertEqual(row['payload'],self.payload)
        self.assertEqual(row['request_id'],request)
