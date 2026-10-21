from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepare_release as release

class RuntimeResourcesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'_app/locales').mkdir(parents=True)
        (self.root/'_app/i18n.py').write_text('pass\n')
        for lang in ('fr','en'):(self.root/f'_app/locales/{lang}.json').write_text('{"label":"Fictional"}')
        self.files=[Path('_app/i18n.py'),Path('_app/locales/fr.json'),Path('_app/locales/en.json')]
    def test_missing_locale_blocks_before_output(self):
        with patch.object(release,'RACINE',self.root),patch.object(release,'DIST_DIR',self.root/'output'):
            with self.assertRaisesRegex(RuntimeError,'catalogue de langue absent'):
                release.construire_archive('fictional',self.files[:-1])
        self.assertFalse((self.root/'output').exists())
    def test_invalid_duplicate_or_mismatched_translations_are_rejected(self):
        for content in ('broken','[]','{}','{"label":null}','{"label":"first","label":"second"}','{"other":"Fictional"}'):
            (self.root/'_app/locales/en.json').write_text(content)
            with self.subTest(content=content),patch.object(release,'RACINE',self.root):
                with self.assertRaisesRegex(RuntimeError,'catalogue'):release.verifier_liste_archive(self.files)
    def test_explicit_local_module_check_writes_no_archive_or_manifest(self):
        (self.root/'_app/entry.py').write_text('import added_module\n')
        (self.root/'_app/added_module.py').write_text('pass\n')
        with patch.object(release,'RACINE',self.root),patch.object(release,'lister_fichiers_suivis',return_value=[Path('_app/entry.py')]),patch.object(release,'construire_archive',side_effect=AssertionError('archive')),patch.object(release,'ecrire_manifest_pret',side_effect=AssertionError('manifest')):
            self.assertEqual(release.main(['--check-files','--additional-file','_app/added_module.py']),0)
    def test_additional_files_cannot_bypass_official_release_selection(self):
        with patch.object(release,'verifier_arbre_propre',side_effect=AssertionError('not a build')):
            with self.assertRaises(SystemExit):release.main(['--additional-file','_app/added_module.py'])

if __name__=='__main__':unittest.main()
