"""Préparation réelle sur une installation fictive ; aucun téléchargement réseau."""
import hashlib
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_app'))
import update_gruterra as updater

class TestPreparationUpdate(unittest.TestCase):
    def test_preparation_verifie_et_sauvegarde_sans_remplacer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'installed';root.mkdir();(root/'app.txt').write_text('old')
            archive=Path(d)/'official.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('gruterra/app.txt','new')
                z.writestr('gruterra/plantes.db','do not import')
            diag={'statut_global':'pret_a_verifier','version':{'statut':'mise_a_jour_disponible','manifest_auto_update':True,'archive_url':'https://example.test/a.zip','sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}}
            def download(url,dest):dest.write_bytes(archive.read_bytes())
            with patch.object(updater,'telecharger_archive',side_effect=download):
                result=updater.appliquer_mise_a_jour(diag,root,dry_run=True,preparer=True)
            self.assertTrue(result['prepare'])
            self.assertFalse(result['applique'])
            self.assertEqual((root/'app.txt').read_text(),'old')
            self.assertFalse((root/'plantes.db').exists())
            with zipfile.ZipFile(result['backup']) as z:self.assertEqual(z.read('app.txt'),b'old')

    def test_deja_a_jour_ne_telecharge_ni_sauvegarde(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(updater,'telecharger_archive') as download,patch.object(updater,'sauvegarder_programme') as backup:
                result=updater.appliquer_mise_a_jour({'version':{'statut':'a_jour'}},Path(d),preparer=True)
            self.assertFalse(result['ok']);download.assert_not_called();backup.assert_not_called()

    def test_mauvaise_empreinte_ne_cree_pas_de_sauvegarde(self):
        with tempfile.TemporaryDirectory() as d:
            diag={'version':{'statut':'mise_a_jour_disponible','manifest_auto_update':True,'archive_url':'https://example.test/a.zip','sha256':'a'*64}}
            with patch.object(updater,'telecharger_archive',side_effect=lambda url,dest:dest.write_bytes(b'corrupted')),patch.object(updater,'sauvegarder_programme') as backup:
                with self.assertRaises(RuntimeError):updater.appliquer_mise_a_jour(diag,Path(d),preparer=True)
                backup.assert_not_called()

    def test_apply_never_overwrites_database_or_private_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'installed';root.mkdir()
            private_names=['_app/plantes.db','custom/observations.sqlite3','custom/observations.sqlite3-wal',
                           'BOTANEO.LOCAL.JSON','_USER_BACKUPS/saved.json','_CONFIG/private.json']
            for name in private_names:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(b'private-original')
            archive=Path(directory)/'package.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('gruterra/program.py','new-program')
                for name in private_names:z.writestr('gruterra/'+name,'must-not-replace')
            diag={'version':{'statut':'mise_a_jour_disponible','manifest_auto_update':True,
                            'archive_url':'https://example.test/test.zip',
                            'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}}
            with patch.object(updater,'telecharger_archive',side_effect=lambda url,dest:dest.write_bytes(archive.read_bytes())):
                result=updater.appliquer_mise_a_jour(diag,root,dry_run=False)
            self.assertTrue(result['applique'])
            self.assertEqual((root/'program.py').read_text(),'new-program')
            for name in private_names:
                with self.subTest(path=name):self.assertEqual((root/name).read_bytes(),b'private-original')

    def test_backups_created_in_same_second_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'program.py';target.write_text('first')
            with patch.object(updater,'datetime') as clock:
                clock.now.return_value.strftime.return_value='20261017-120000'
                first=updater.sauvegarder_programme(root,[Path('program.py')])
                target.write_text('second')
                second=updater.sauvegarder_programme(root,[Path('program.py')])
            self.assertNotEqual(first,second)
            with zipfile.ZipFile(first) as z:self.assertEqual(z.read('program.py'),b'first')
            with zipfile.ZipFile(second) as z:self.assertEqual(z.read('program.py'),b'second')
