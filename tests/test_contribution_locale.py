import json
import os
import sys
import tempfile
import zipfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import contribution_locale as module
from sauvegarde_utilisateur import creer_sauvegarde_utilisateur

class ContributionLocaleTests(unittest.TestCase):
    def test_key_is_durable_and_not_created_by_information(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module,'CONFIG_DIR',Path(folder)), patch.dict(os.environ,{'BOTANEO_DEMO':'0'}):
            module.marquer_information_lue()
            self.assertNotIn('management_key',module.lire_etat())
            first=module.preparer_identite()
            self.assertEqual(first,module.preparer_identite())
            self.assertFalse(module.lire_etat()['sharing_enabled'])

    def test_demo_never_creates_identity_or_information_state(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module,'CONFIG_DIR',Path(folder)), patch.dict(os.environ,{'BOTANEO_DEMO':'1'}):
            with self.assertRaises(ValueError):module.preparer_identite()
            module.marquer_information_lue()
            self.assertFalse(module.chemin().exists())

    def test_corrupt_key_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module,'CONFIG_DIR',Path(folder)), patch.dict(os.environ,{'BOTANEO_DEMO':'0'}):
            module.chemin().write_text('{"management_key":"broken"}',encoding='utf-8')
            before=module.chemin().read_bytes()
            with self.assertRaises(ValueError):module.preparer_identite()
            self.assertEqual(before,module.chemin().read_bytes())

    def test_private_key_in_full_backup_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'_config').mkdir()
            (root/'_config/contribution.local.json').write_text('{}')
            full=creer_sauvegarde_utilisateur(root,'complete',root/'full')
            shared=creer_sauvegarde_utilisateur(root,'donnees',root/'shared')
            with zipfile.ZipFile(full) as archive:
                self.assertIn('_config/contribution.local.json',archive.namelist())
            with zipfile.ZipFile(shared) as archive:
                self.assertNotIn('_config/contribution.local.json',archive.namelist())

    def test_restore_on_fresh_install_and_repeat_preserve_identity(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'CONFIG_DIR', Path(folder)), patch.dict(os.environ, {'BOTANEO_DEMO': '0'}):
            identity = {'schema_version': 1, 'contributor_id': 'a' * 43, 'management_key': 'b' * 43}
            module.marquer_information_lue()
            self.assertEqual(identity, module.restaurer_identite(identity))
            self.assertEqual(identity, module.restaurer_identite(identity))
            state = module.lire_etat()
            self.assertTrue(state['information_seen'])
            self.assertFalse(state['sharing_enabled'])

    def test_restore_rejects_changes_to_either_part_without_writing(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'CONFIG_DIR', Path(folder)), patch.dict(os.environ, {'BOTANEO_DEMO': '0'}):
            identity = module.preparer_identite()
            before = module.chemin().read_bytes()
            for field in ('contributor_id', 'management_key'):
                with self.subTest(field=field):
                    changed = dict(identity, **{field: 'x' * 43})
                    with self.assertRaises(ValueError):
                        module.restaurer_identite(changed)
                    self.assertEqual(before, module.chemin().read_bytes())

    def test_restore_preserves_incomplete_or_unreadable_existing_state(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'CONFIG_DIR', Path(folder)), patch.dict(os.environ, {'BOTANEO_DEMO': '0'}):
            identity = {'schema_version': 1, 'contributor_id': 'a' * 43, 'management_key': 'b' * 43}
            for content in ('{"management_key":"broken"}', '{not json'):
                module.chemin().write_text(content, encoding='utf-8')
                before = module.chemin().read_bytes()
                with self.assertRaises((ValueError, RuntimeError)):
                    module.restaurer_identite(identity)
                self.assertEqual(before, module.chemin().read_bytes())

    def test_demo_restore_cannot_import_real_identity(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(module, 'CONFIG_DIR', Path(folder)), patch.dict(os.environ, {'BOTANEO_DEMO': '1'}):
            identity = {'schema_version': 1, 'contributor_id': 'a' * 43, 'management_key': 'b' * 43}
            with self.assertRaises(ValueError):
                module.restaurer_identite(identity)
            self.assertFalse(module.chemin().exists())
