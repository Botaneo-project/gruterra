import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

module_path=Path(__file__).resolve().parents[1]/'prepare_release.py'
spec=importlib.util.spec_from_file_location('release_under_test',module_path)
release=importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

class ReleaseContentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'_app').mkdir()
        (self.root/'_app/interface.py').write_text('import ui_palette\n',encoding='utf-8')
        (self.root/'_app/ui_palette.py').write_text('THEME = {}\n',encoding='utf-8')
    def test_missing_palette_blocks_zip_before_any_output(self):
        with patch.object(release,'RACINE',self.root), patch.object(release,'DIST_DIR',self.root/'_dist'):
            with self.assertRaisesRegex(RuntimeError,'module local absent'):
                release.construire_archive('fictitious',[Path('_app/interface.py')])
        self.assertFalse((self.root/'_dist').exists())
    def test_private_file_refused_even_if_explicitly_supplied(self):
        for relative in ['_config/private.local.json','_app/data/demo/plantes_demo.db','_security_backups/copy.py','discord_bot/bot.py','public/data.sqlite3']:
            path=self.root/relative
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('fictional',encoding='utf-8')
            with self.subTest(path=relative), patch.object(release,'RACINE',self.root), self.assertRaisesRegex(RuntimeError,'privé'):
                release.verifier_liste_archive([Path(relative)])
    def test_public_code_and_empty_template_allowed(self):
        target=self.root/'docs/examples/home_assistant.local.json.example'
        target.parent.mkdir(parents=True)
        target.write_text('{}',encoding='utf-8')
        files=[Path('_app/interface.py'),Path('_app/ui_palette.py'),target.relative_to(self.root)]
        with patch.object(release,'RACINE',self.root), patch.object(release,'DIST_DIR',self.root/'_dist'):
            archive=release.construire_archive('fictitious',files)
            self.assertTrue(archive.is_file())
    def test_check_mode_does_not_require_clean_tree_or_write_manifest(self):
        files=[Path('_app/interface.py'),Path('_app/ui_palette.py')]
        with patch.object(release,'RACINE',self.root), patch.object(release,'lister_fichiers_suivis',return_value=files), patch.object(release,'verifier_arbre_propre',side_effect=AssertionError('not a build')), patch.object(release,'ecrire_manifest_pret',side_effect=AssertionError('manifest write')):
            self.assertEqual(release.main(['--check-files']),0)
    def test_relative_escape_refused(self):
        with patch.object(release,'RACINE',self.root), self.assertRaises(RuntimeError):
            release.verifier_liste_archive([Path('../private.py')])

    def test_subprocess_restart_helper_required_before_zip_creation(self):
        (self.root/'_app/interface.py').write_text("HELPER = 'restart_gruterra.py'\n",encoding='utf-8')
        # Test both an omitted existing helper and a missing source helper.
        helper=self.root/'_app/restart_gruterra.py'
        for exists in (True,False):
            if exists:helper.write_text('pass\n',encoding='utf-8')
            elif helper.exists():helper.unlink()
            with self.subTest(source_exists=exists), patch.object(release,'RACINE',self.root), patch.object(release,'DIST_DIR',self.root/'_dist'):
                with self.assertRaisesRegex(RuntimeError,'assistant de relance absent'):
                    release.construire_archive('fictitious',[Path('_app/interface.py')])
            self.assertFalse((self.root/'_dist').exists())

    def test_complete_restart_helper_selection_is_accepted(self):
        (self.root/'_app/interface.py').write_text("HELPER = 'restart_gruterra.py'\n",encoding='utf-8')
        (self.root/'_app/restart_gruterra.py').write_text('pass\n',encoding='utf-8')
        with patch.object(release,'RACINE',self.root), patch.object(release,'DIST_DIR',self.root/'_dist'):
            archive=release.construire_archive('fictitious',[Path('_app/interface.py'),Path('_app/restart_gruterra.py')])
            self.assertTrue(archive.is_file())

if __name__=='__main__':
    unittest.main()
