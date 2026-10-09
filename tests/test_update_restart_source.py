"""Source du manifeste et relance après libération effective de l'ancienne instance."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_app'))
import botaneo_update
import restart_gruterra
from i18n import utiliser_langue

class TestSourceManifeste(unittest.TestCase):
    def test_github_prime_sur_ancien_manifeste_local(self):
        with tempfile.TemporaryDirectory() as d:
            local=Path(d)/'version.json';local.write_text(json.dumps({'version':'0.1.4-dev'}))
            manifest={'disponible':True,'version':'0.1.7-dev','source':'https://raw.githubusercontent.com/Botaneo-project/gruterra/main/version_manifest.json'}
            with patch.object(botaneo_update,'lire_manifest_version_distant',return_value=manifest):
                status=botaneo_update.construire_statut_version('0.1.6-dev',chemin_manifest_local=local,url_manifest_distant=manifest['source'],verifier_distant=True)
            self.assertEqual(status['type_source'],'github')
            self.assertEqual(status['version_distante'],'0.1.7-dev')
            with utiliser_langue('fr'):self.assertIn('Vérifié sur GitHub',botaneo_update.formater_source_verification(status))

    def test_repli_local_explicitement_identifie(self):
        with tempfile.TemporaryDirectory() as d:
            local=Path(d)/'version.json';local.write_text(json.dumps({'version':'0.1.4-dev'}))
            with patch.object(botaneo_update,'lire_manifest_version_distant',return_value={'disponible':False,'source':'https://github.test','message':'Network unavailable'}):
                status=botaneo_update.construire_statut_version('0.1.6-dev',chemin_manifest_local=local,url_manifest_distant='https://github.test',verifier_distant=True)
            self.assertEqual(status['type_source'],'repli_local')
            self.assertEqual(status['version_distante'],'0.1.4-dev')
            for lang,phrase in [('fr','Vérification en ligne impossible'),('en','Online check unavailable')]:
                with utiliser_langue(lang):self.assertIn(phrase,botaneo_update.formater_source_verification(status))

    def test_repli_local_ne_permet_pas_installation(self):
        import update_gruterra
        diag={'version':{'type_source':'repli_local','statut':'mise_a_jour_disponible','archive_url':'https://github.test/a.zip','sha256':'a'*64,'manifest_auto_update':True}}
        ok,_=update_gruterra.valider_manifest_applicable(diag)
        self.assertFalse(ok)

class TestRedemarrage(unittest.TestCase):
    def test_attend_sortie_reelle_processus_windows(self):
        process=subprocess.Popen([sys.executable,'-c','import time; time.sleep(0.4)'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            self.assertFalse(restart_gruterra.attendre_fin_processus(process.pid,0.01))
            self.assertTrue(restart_gruterra.attendre_fin_processus(process.pid,5))
        finally:process.wait(timeout=5)

    def test_timeout_ne_lance_rien(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'Lancer_Demo.py').write_text('')
            with patch.object(restart_gruterra,'attendre_fin_processus',return_value=False),patch.object(restart_gruterra.subprocess,'Popen') as launch:
                with self.assertRaises(TimeoutError):restart_gruterra.relancer_apres_sortie(123,'demo',Path(d))
                launch.assert_not_called()

    def test_mode_et_attente_avant_lancement_unique(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for mode,filename in [('demo','Lancer_Demo.py'),('real','Lancer_Gruterra.py')]:
                (root/filename).write_text('')
                order=[]
                with patch.object(restart_gruterra,'attendre_fin_processus',side_effect=lambda *a:order.append('exit') or True),patch.object(restart_gruterra.subprocess,'Popen',side_effect=lambda *a,**kw:order.append('launch')) as launch:
                    restart_gruterra.relancer_apres_sortie(123,mode,root)
                self.assertEqual(order,['exit','launch'])
                launch.assert_called_once()
                self.assertEqual(launch.call_args.args[0],[sys.executable,str(root/filename)])

    def test_helper_reel_attend_liberation_du_verrou(self):
        import shutil
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            root=Path(d);app=root/'_app';app.mkdir()
            shutil.copyfile(ROOT/'_app/restart_gruterra.py',app/'restart_gruterra.py')
            lock=root/'instance.lock';ready=root/'ready';release=root/'release';marker=root/'restarted'
            imports=f"import sys; sys.path.insert(0,{str(ROOT/'_app')!r}); from instance_botaneo import VerrouInstance; from pathlib import Path; import time; "
            old_code=imports+f"lock=VerrouInstance(Path({str(lock)!r})); lock.acquerir(); Path({str(ready)!r}).write_text('ready');\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\nlock.liberer()"
            launcher=imports+f"lock=VerrouInstance(Path({str(lock)!r})); lock.acquerir(); Path({str(marker)!r}).write_text('demo'); lock.liberer()"
            (root/'Lancer_Demo.py').write_text(launcher)
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
            old=subprocess.Popen([sys.executable,'-c',old_code],creationflags=flags)
            helper=None
            try:
                deadline=time.monotonic()+5
                while not ready.exists() and time.monotonic()<deadline:time.sleep(0.02)
                self.assertTrue(ready.exists())
                helper=subprocess.Popen([sys.executable,str(app/'restart_gruterra.py'),'--parent-pid',str(old.pid),'--mode','demo'],creationflags=flags)
                time.sleep(0.1);self.assertFalse(marker.exists())
                release.write_text('exit');old.wait(timeout=5)
                self.assertEqual(helper.wait(timeout=5),0)
                deadline=time.monotonic()+5
                while not marker.exists() and time.monotonic()<deadline:time.sleep(0.02)
                self.assertEqual(marker.read_text(),'demo')
            finally:
                if old.poll() is None:old.terminate();old.wait(timeout=5)
                if helper is not None and helper.poll() is None:helper.terminate();helper.wait(timeout=5)
