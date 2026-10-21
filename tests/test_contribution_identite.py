import base64
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
import contribution_identite as module
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from sauvegarde_utilisateur import creer_sauvegarde_utilisateur


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        for context in (patch.object(module, 'CONFIG_DIR', self.root / '_config'),
                        patch.dict(os.environ, {'BOTANEO_DEMO': '0'})):
            context.start()
            self.addCleanup(context.stop)

    def test_durable_identity_and_signature(self):
        identity = module.preparer_identite()
        self.assertEqual(identity, module.preparer_identite())
        public = module.identite_publique()
        self.assertEqual(set(public), {'contributor_id', 'public_key'})
        raw = base64.b64decode(public['public_key'], validate=True)
        self.assertEqual(len(raw), 32)
        self.assertTrue(public['public_key'].endswith('='))
        self.assertEqual(public['contributor_id'], 'ed25519:' + hashlib.sha256(raw).hexdigest())
        message = 'é è à ç œ ’ — → 🇫🇷 🌱'.encode('utf-8')
        signature = base64.b64decode(module.signer(message), validate=True)
        self.assertEqual(len(signature), 64)
        Ed25519PublicKey.from_public_bytes(raw).verify(signature, message)
        with self.assertRaises(InvalidSignature):
            Ed25519PublicKey.from_public_bytes(raw).verify(signature, message + b'!')

    def test_encrypted_backup_and_new_install(self):
        backup = self.root / 'backup.json'
        module.sauvegarder(backup, 'mot de passe test éphémère')
        identity = module.preparer_identite()
        data = json.loads(backup.read_text(encoding='utf-8'))
        self.assertNotIn('private_seed_b64', data)
        self.assertNotIn(identity['private_seed_b64'], backup.read_text(encoding='utf-8'))
        module.chemin().unlink()
        with self.assertRaises(ValueError):
            module.restaurer_sauvegarde(data, 'incorrect')
        self.assertFalse(module.chemin().exists())
        self.assertEqual(identity, module.restaurer_sauvegarde(data, 'mot de passe test éphémère'))
        self.assertEqual(identity, module.restaurer_sauvegarde(data, 'mot de passe test éphémère'))
        with self.assertRaises(ValueError):
            module.sauvegarder(backup, 'autre')

    def test_invalid_pair_or_replacement_preserves_existing(self):
        identity = module.preparer_identite()
        before = module.chemin().read_bytes()
        for field in ('public_key', 'contributor_id', 'private_seed_b64'):
            invalid = dict(identity)
            invalid[field] = 'invalid'
            with self.assertRaises(ValueError):
                module.restaurer_identite(invalid)
            self.assertEqual(before, module.chemin().read_bytes())
        with patch.object(module, 'CONFIG_DIR', self.root/'other'):
            other = module.preparer_identite()
        with self.assertRaises(ValueError):
            module.restaurer_identite(other)
        self.assertEqual(before, module.chemin().read_bytes())

    def test_legacy_identity_not_replaced_or_reinterpreted(self):
        module.CONFIG_DIR.mkdir()
        legacy = module.CONFIG_DIR/'contribution.local.json'
        legacy.write_text('{"schema_version":1,"contributor_id":"legacy","management_key":"legacy"}')
        before = legacy.read_bytes()
        with self.assertRaises(ValueError):
            module.preparer_identite()
        self.assertEqual(before, legacy.read_bytes())
        self.assertFalse(module.chemin().exists())

    def test_demo_blocks_generation_restoration_signing_and_backup(self):
        identity = module.preparer_identite()
        before = module.chemin().read_bytes()
        with patch.dict(os.environ, {'BOTANEO_DEMO':'1'}):
            for operation in (module.preparer_identite, module.identite_publique,
                              lambda: module.restaurer_identite(identity),
                              lambda: module.signer(b'test'),
                              lambda: module.sauvegarder(self.root/'forbidden.json','test'),
                              lambda: module.restaurer_sauvegarde({},'test')):
                with self.assertRaises(ValueError):
                    operation()
        self.assertEqual(before, module.chemin().read_bytes())
        self.assertFalse((self.root/'forbidden.json').exists())

    def test_corrupt_file_and_lock_do_not_regenerate(self):
        module.CONFIG_DIR.mkdir()
        module.chemin().write_text('{invalid')
        with self.assertRaises(RuntimeError):
            module.preparer_identite()
        self.assertEqual(module.chemin().read_text(), '{invalid')
        module.chemin().unlink()
        lock = module.chemin().with_suffix('.lock')
        lock.touch()
        with self.assertRaises(RuntimeError):
            module.preparer_identite()
        self.assertFalse(module.chemin().exists())

    def test_private_identity_in_full_backup_only(self):
        module.preparer_identite()
        import sqlite3
        (self.root/'_app').mkdir(exist_ok=True)
        with sqlite3.connect(self.root/'_app/plantes.db') as backup_fixture:
            backup_fixture.execute('CREATE TABLE fictive (id INTEGER)')
        backup_fixture.close()
        full = creer_sauvegarde_utilisateur(self.root, 'complete', self.root/'full')
        shared = creer_sauvegarde_utilisateur(self.root, 'donnees', self.root/'shared')
        import zipfile
        with zipfile.ZipFile(full) as archive:
            self.assertIn('_config/contribution.identity.local.json', archive.namelist())
        with zipfile.ZipFile(shared) as archive:
            self.assertNotIn('_config/contribution.identity.local.json', archive.namelist())
