"""Kill real child processes on invented installations, then recover offline."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import update_recovery as recovery

CHILD = r"""
from pathlib import Path
import json,os,sys
sys.path.insert(0,sys.argv[1])
import update_gruterra as updater
import update_recovery
from unittest.mock import patch
root=Path(sys.argv[2]); archive=Path(sys.argv[3]); mode=sys.argv[4]
diagnostic={'version':{'statut':'mise_a_jour_disponible','manifest_auto_update':True,
    'archive_url':'https://example.invalid/fixture.zip','sha256':updater.calculer_sha256(archive)}}
original=updater.remplacer_fichier
def interrupted(source,destination,*args):
    if mode=='staging':
        Path(args[0]).parent.mkdir(parents=True,exist_ok=True)
        Path(args[0]).write_bytes(b'incomplete staged file')
        os._exit(91)
    original(source,destination,*args)
    if Path(destination).name=='update_recovery.py' and mode=='apply':os._exit(91)
if mode=='commit':update_recovery.clear=lambda root:os._exit(92)
with patch.object(updater,'telecharger_archive',side_effect=lambda url,dest:dest.write_bytes(archive.read_bytes())),patch.object(updater,'remplacer_fichier',side_effect=interrupted):
    result=updater.appliquer_mise_a_jour(diagnostic,root,dry_run=False)
print(json.dumps(result))
"""

class CrashRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'installed';self.root.mkdir()
        (self.root/'_app').mkdir();(self.root/'_config').mkdir()
        for name in ('Lancer_Demo.py','Lancer_Gruterra.py','update_recovery.py'):
            shutil.copyfile(ROOT/name,self.root/name)
        (self.root/'a.py').write_bytes(b'old program')
        marker_code="from pathlib import Path; (Path(__file__).resolve().parent.parent/'started.txt').write_text('started')"
        (self.root/'_app/lancer_demo.py').write_text(marker_code)
        (self.root/'_app/interface.py').write_text(marker_code)
        self.private={'_app/plantes.db':b'private database','_config/settings.local.json':b'private settings'}
        for name,content in self.private.items():(self.root/name).write_bytes(content)
        self.archive=Path(self.tmp.name)/'fixture.zip'
        with zipfile.ZipFile(self.archive,'w') as package:
            package.writestr('package/a.py','new program')
            package.writestr('package/new.py','newly added')
            # The frozen runner must work even if the program recovery module
            # was replaced by an incompatible (but valid Python) version.
            package.writestr('package/update_recovery.py',"raise RuntimeError('simulated incompatible helper')")
            for name in self.private:package.writestr('package/'+name,'must not replace')
    def interrupt(self,mode='apply'):
        result=subprocess.run([sys.executable,'-X','utf8','-B','-c',CHILD,str(ROOT),str(self.root),str(self.archive),mode],capture_output=True,text=True,encoding='utf-8',timeout=25)
        self.assertEqual(result.returncode,92 if mode=='commit' else 91,result.stderr)
        self.assertTrue((self.root/'_security_backups'/recovery.MARKER).is_file())
        return self.root/'_security_backups'/recovery.MARKER
    def start(self,name='Lancer_Demo.py'):
        return subprocess.run([sys.executable,'-X','utf8','-B',str(self.root/name)],cwd=self.root,capture_output=True,text=True,encoding='utf-8',timeout=25)
    def assert_private_unchanged(self):
        for name,content in self.private.items():self.assertEqual((self.root/name).read_bytes(),content)
    def test_both_launchers_restore_after_process_killed_during_apply(self):
        # Two separate transactions: restore and retry, without touching user data.
        for launcher in ('Lancer_Demo.py','Lancer_Gruterra.py'):
            with self.subTest(launcher=launcher):
                (self.root/'started.txt').unlink(missing_ok=True)
                journal=self.interrupt()
                self.assertEqual((self.root/'a.py').read_bytes(),b'new program')
                result=self.start(launcher)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertTrue((self.root/'started.txt').exists())
                self.assertFalse(journal.exists())
                self.assertEqual((self.root/'a.py').read_bytes(),b'old program')
                self.assertFalse((self.root/'new.py').exists())
                self.assertEqual((self.root/'update_recovery.py').read_bytes(),(ROOT/'update_recovery.py').read_bytes())
                self.assertIn('previous version restored',result.stdout)
                self.assert_private_unchanged()
    def test_kill_during_staging_leaves_original_and_cleans_known_temp_file(self):
        journal=self.interrupt('staging')
        self.assertTrue(list(self.root.glob('.gruterra-update-*')))
        result=self.start();self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(journal.exists());self.assertFalse(list(self.root.glob('.gruterra-update-*')))
        self.assertEqual((self.root/'a.py').read_bytes(),b'old program');self.assert_private_unchanged()
    def test_committed_update_survives_kill_before_marker_cleanup(self):
        journal=self.interrupt('commit');data=json.loads(journal.read_text())
        self.assertEqual(data['state'],'committed')
        result=self.start();self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(journal.exists());self.assertEqual((self.root/'a.py').read_bytes(),b'new program')
        self.assertTrue((self.root/'new.py').exists());self.assert_private_unchanged()
    def test_corrupted_backup_blocks_startup_and_keeps_evidence(self):
        journal=self.interrupt();data=json.loads(journal.read_text())
        backup=journal.parent/data['backup']
        with backup.open('ab') as stream:stream.write(b'corrupted')
        result=self.start()
        self.assertEqual(result.returncode,3)
        self.assertFalse((self.root/'started.txt').exists())
        self.assertTrue(journal.exists());self.assertTrue(backup.exists());self.assert_private_unchanged()
    def test_journal_cannot_target_private_files_or_escape_installation(self):
        journal=self.interrupt();original=json.loads(journal.read_text())
        for name in ('_app/plantes.db','_CONFIG/settings.local.json','../outside.txt','C:/outside.txt'):
            with self.subTest(path=name):
                data=json.loads(json.dumps(original));data['files'][0]['path']=name;data['attempted'][0]=name
                journal.write_text(json.dumps(data))
                result=self.start();self.assertEqual(result.returncode,3)
                self.assertFalse((self.root/'started.txt').exists());self.assert_private_unchanged()
        journal.write_text(json.dumps(original))
        self.assertEqual(self.start().returncode,0)
    def test_startup_refuses_live_updater_even_before_a_journal_exists(self):
        with recovery.update_lock(self.root):
            result=self.start()
        self.assertEqual(result.returncode,3)
        self.assertFalse((self.root/'started.txt').exists())
        self.assertEqual(self.start().returncode,0)
    def test_rollback_can_itself_be_interrupted_then_retried(self):
        journal=self.interrupt()
        code=r"""
from pathlib import Path
import os,runpy,sys
root=Path(sys.argv[1]); runner=root/'_security_backups/update-recovery.py'
module=runpy.run_path(str(runner)); original=os.replace
def interrupted(source,destination):
    original(source,destination)
    if Path(destination).name=='update_recovery.py':os._exit(93)
os.replace=interrupted
module['recover_pending'](root)
"""
        result=subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(self.root)],capture_output=True,timeout=25)
        self.assertEqual(result.returncode,93);self.assertTrue(journal.exists())
        self.assertEqual(self.start().returncode,0)
        self.assertFalse(journal.exists());self.assertEqual((self.root/'a.py').read_bytes(),b'old program')
        self.assert_private_unchanged()
    def test_unexpected_new_file_is_not_deleted_to_force_recovery(self):
        journal=self.interrupt();(self.root/'new.py').write_bytes(b'unrelated local edit')
        result=self.start();self.assertEqual(result.returncode,3)
        self.assertEqual((self.root/'new.py').read_bytes(),b'unrelated local edit')
        self.assertTrue(journal.exists());self.assert_private_unchanged()
