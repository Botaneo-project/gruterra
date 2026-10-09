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
