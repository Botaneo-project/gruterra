"""Failure recovery with invented installations; no network or user data."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_app'))
import update_gruterra as updater


class UpdateTransactionTests(unittest.TestCase):
    def apply(self, folder, changes):
        archive = folder / 'package.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            for name, content in changes.items():
                z.writestr('package/' + name, content)
        diagnostic = {'version': {'statut': 'mise_a_jour_disponible',
            'manifest_auto_update': True, 'archive_url': 'https://example.invalid/package.zip',
            'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}}
        with patch.object(updater, 'telecharger_archive', side_effect=lambda url, dest: dest.write_bytes(archive.read_bytes())):
            return updater.appliquer_mise_a_jour(diagnostic, folder / 'installed', dry_run=False)

    def test_failure_restores_existing_files_and_removes_new_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory); installed = folder / 'installed'; installed.mkdir()
            (installed / 'b.py').write_bytes(b'old-b')
            (installed / 'z.py').write_bytes(b'old-z')
            (installed / 'plantes.db').write_bytes(b'private database')
            original = updater.os.replace
            def fail_last(source, destination):
                if Path(destination).name == 'z.py':
                    raise PermissionError('simulated locked file')
                return original(source, destination)
            with patch.object(updater.os, 'replace', side_effect=fail_last):
                result = self.apply(folder, {'a-new.py':'new', 'b.py':'new-b', 'z.py':'new-z', 'plantes.db':'forbidden'})
            self.assertFalse(result['ok']); self.assertFalse(result['applique']); self.assertTrue(result['restaure'])
            self.assertFalse((installed / 'a-new.py').exists())
            self.assertEqual((installed / 'b.py').read_bytes(), b'old-b')
            self.assertEqual((installed / 'z.py').read_bytes(), b'old-z')
            self.assertEqual((installed / 'plantes.db').read_bytes(), b'private database')
            self.assertFalse(list(installed.rglob('.gruterra-update-*')))
            with zipfile.ZipFile(result['backup']) as backup:
                self.assertEqual(backup.read('b.py'), b'old-b')

    def test_failed_staging_never_truncates_installed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory); installed=folder/'installed'; installed.mkdir()
            (installed/'app.py').write_bytes(b'old-complete')
            def partial_write(source, destination):
                Path(destination).write_bytes(b'partial')
                raise OSError('simulated full volume')
            with patch.object(updater.shutil, 'copy2', side_effect=partial_write):
                result=self.apply(folder, {'app.py':'new-complete'})
            self.assertFalse(result['ok']); self.assertTrue(result['restaure'])
            self.assertEqual((installed/'app.py').read_bytes(), b'old-complete')
            self.assertFalse(list(installed.rglob('.gruterra-update-*')))

    def test_failed_restore_reports_incomplete_recovery_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory); installed=folder/'installed'; installed.mkdir()
            for name in ('a.py', 'z.py'): (installed/name).write_bytes(b'old')
            original=updater.os.replace
            def failure(source, destination):
                if Path(destination).name=='z.py' or Path(source).read_bytes()==b'old':
                    raise PermissionError('simulated persistent lock')
                return original(source, destination)
            with patch.object(updater.os, 'replace', side_effect=failure):
                result=self.apply(folder, {'a.py':'new', 'z.py':'new'})
            self.assertFalse(result['ok']); self.assertFalse(result['restaure'])
            self.assertEqual(result['fichiers_a_restaurer'], ['a.py'])
            with zipfile.ZipFile(result['backup']) as backup:
                self.assertEqual(backup.read('a.py'), b'old')

    def test_success_commits_all_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory); (folder/'installed').mkdir()
            result=self.apply(folder, {'a.py':'new-a', 'b.py':'new-b'})
            self.assertTrue(result['ok']); self.assertEqual(result['fichiers'],2)
            self.assertEqual((folder/'installed/b.py').read_text(), 'new-b')
