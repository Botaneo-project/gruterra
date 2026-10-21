"""Restore synthetic snapshots, including committed WAL data and external paths."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from contextlib import closing

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'_app'))
from sauvegarde_utilisateur import creer_sauvegarde_utilisateur


class ActiveBackupTests(unittest.TestCase):
    def test_external_wal_snapshot_can_be_opened_independently(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'installation';root.mkdir()
            source=Path(folder)/'external.sqlite3'
            writer=sqlite3.connect(source)
            try:
                writer.execute('PRAGMA journal_mode=WAL')
                writer.execute('CREATE TABLE fictive (value TEXT)')
                writer.execute("INSERT INTO fictive VALUES ('committed')")
                writer.commit()
                with patch.dict(os.environ, {'BOTANEO_DB_PATH':str(source)}):
                    archive=creer_sauvegarde_utilisateur(root,'donnees')
                restored=Path(folder)/'restored.sqlite3'
                with zipfile.ZipFile(archive) as z:
                    restored.write_bytes(z.read('_app/plantes.db'))
                    manifest=json.loads(z.read('MANIFEST_GRUTERRA_BACKUP.json'))
                    self.assertNotIn(str(source),json.dumps(manifest))
                    self.assertFalse(any(n.endswith(('-wal','-shm')) for n in z.namelist()))
                with closing(sqlite3.connect(restored)) as check:
                    self.assertEqual(check.execute('SELECT * FROM fictive').fetchall(),[('committed',)])
                    self.assertEqual(check.execute('PRAGMA integrity_check').fetchone(),('ok',))
            finally:
                writer.close()

    def test_missing_active_db_does_not_fall_back_to_root_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'plantes.db').write_text('legacy')
            with self.assertRaises(FileNotFoundError):
                creer_sauvegarde_utilisateur(root, db_path=root/'_app/plantes.db')
            self.assertFalse(list(root.rglob('*.zip')))

    def test_invalid_database_leaves_no_success_archive_or_temporary_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'invalid.db';source.write_text('not sqlite')
            with self.assertRaises(sqlite3.DatabaseError):
                creer_sauvegarde_utilisateur(root,db_path=source)
            self.assertEqual(list((root/'_user_backups').iterdir()),[])

    def test_explicit_db_wins_over_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'chosen.db'
            with closing(sqlite3.connect(source)) as db:db.execute('CREATE TABLE fictive (id INTEGER)')
            with patch.dict(os.environ,{'BOTANEO_DB_PATH':str(root/'missing.db')}):
                archive=creer_sauvegarde_utilisateur(root,db_path=source)
            self.assertTrue(archive.is_file())

    def test_custom_config_and_data_are_included_without_private_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'install';root.mkdir()
            config=Path(folder)/'config';config.mkdir()
            data=Path(folder)/'data';data.mkdir()
            (config/'fictional.local.json').write_text('{"fictional":true}')
            (data/'observation.txt').write_text('fictional')
            nested=data/'demo/config';nested.mkdir(parents=True)
            (nested/'fictional.local.json').write_text('{}')
            old=data/'demo/_user_backups';old.mkdir()
            (old/'private.zip').write_bytes(b'fictional private backup')
            source=root/'active.bin'
            with closing(sqlite3.connect(source)) as db:db.execute('CREATE TABLE fictive (id INTEGER)')
            kwargs=dict(db_path=source,config_dir=config,data_dir=data)
            private=creer_sauvegarde_utilisateur(root,'complete',**kwargs)
            shared=creer_sauvegarde_utilisateur(root,'donnees',**kwargs)
            with zipfile.ZipFile(private) as z:
                self.assertIn('_config/fictional.local.json',z.namelist())
                self.assertIn('_app/data/observation.txt',z.namelist())
            with zipfile.ZipFile(shared) as z:
                self.assertIn('_app/data/observation.txt',z.namelist())
                self.assertFalse(any('config/' in n or n.endswith('.zip') for n in z.namelist()))
