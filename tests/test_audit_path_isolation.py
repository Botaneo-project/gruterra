import ast
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import json
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'_app'))
from raspberry_paths import remote_command, remote_backup, validate_home


class DemoPathTests(unittest.TestCase):
    def test_demo_lock_is_separate_but_real_updater_lock_stays_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            ns={'Path':Path,'os':os,'CONFIG_DIR':root/'custom-config','__file__':str(root/'_app/instance_botaneo.py')}
            tree=ast.parse((ROOT/'_app/instance_botaneo.py').read_text(encoding='utf-8'))
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='VerrouInstance')
            exec(compile(ast.Module(body=[cls],type_ignores=[]),'lock-path','exec'),ns)
            with patch.dict(os.environ,{'BOTANEO_DEMO':'0'}):
                self.assertEqual(ns['VerrouInstance']().path,root/'_config/botaneo.instance.lock')
            with patch.dict(os.environ,{'BOTANEO_DEMO':'1'}):
                self.assertEqual(ns['VerrouInstance']().path,root/'custom-config/botaneo.instance.lock')

    def test_demo_ignores_real_overrides_and_keeps_real_settings_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);app=root/'_app';app.mkdir()
            real=root/'_config';real.mkdir()
            sentinel=real/'interface_layout.local.json';sentinel.write_bytes(b'private sentinel')
            ns={'__file__':str(app/'botaneo_config.py'),'__name__':'isolated_config'}
            with patch.dict(os.environ,{'BOTANEO_DEMO':'1','BOTANEO_CONFIG_DIR':str(real),'BOTANEO_DATA_DIR':str(root/'real-data')}):
                exec(compile((ROOT/'_app/botaneo_config.py').read_text(encoding='utf-8'), ns['__file__'],'exec'),ns)
            self.assertEqual(ns['CONFIG_DIR'], app/'data/demo/config')
            self.assertEqual(ns['DATA_DIR'], app/'data/demo')
            tree=ast.parse((ROOT/'_app/interface.py').read_text(encoding='utf-8'))
            names={'NETATMO_CACHE','PREVISION_CACHE','AUTO_SYNC_CONFIG','NETATMO_UI_CONFIG','INTERFACE_LAYOUT_CONFIG','ALERTES_CONFIG','HISTORIQUE_IMPORT_CONFIG'}
            nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
            exec(compile(ast.Module(body=nodes,type_ignores=[]),'interface-paths','exec'),ns)
            for name in names:
                self.assertTrue(ns[name].is_relative_to(app/'data/demo'),name)
            ns['CONFIG_DIR'].mkdir(parents=True)
            ns['ecrire_json'](ns['INTERFACE_LAYOUT_CONFIG'],{'fictional':True})
            self.assertEqual(sentinel.read_bytes(),b'private sentinel')
            self.assertEqual(list(real.iterdir()),[sentinel])

    def test_normal_mode_preserves_custom_paths(self):
        ns={'__file__':str(ROOT/'_app/botaneo_config.py'),'__name__':'isolated_config'}
        with patch.dict(os.environ,{'BOTANEO_DEMO':'0','BOTANEO_CONFIG_DIR':'fictional-config','BOTANEO_DATA_DIR':'fictional-data'}):
            exec(compile((ROOT/'_app/botaneo_config.py').read_text(encoding='utf-8'),ns['__file__'],'exec'),ns)
        self.assertEqual(ns['CONFIG_DIR'],Path('fictional-config'))
        self.assertEqual(ns['DATA_DIR'],Path('fictional-data'))


class RaspberryPathTests(unittest.TestCase):
    def test_custom_home_used_for_remote_operations_and_backups(self):
        config={'installation_home':'/srv/gruterra-pi'}
        self.assertEqual(remote_command(config,'sync_export.py','weather_export'),'python3 /srv/gruterra-pi/collector/sync_export.py weather_export')
        self.assertEqual(remote_backup(config,'weather','weather-2026-10-20.sqlite3'),'/srv/gruterra-pi/backups/weather/weather-2026-10-20.sqlite3')
        self.assertEqual(remote_command({},'backup_manifest.py'),'python3 ~/botaneo/collector/backup_manifest.py')

    def test_shell_characters_and_traversal_refused(self):
        for home in ('relative','/','/srv/../private','/srv//app','/srv/a;echo','/srv/$(id)','/srv/a\nb','/srv/a b'):
            with self.subTest(home=home),self.assertRaises(ValueError):
                validate_home({'installation_home':home})

    def test_installed_utility_derives_custom_root_without_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            module_path=Path(folder)/'custom/collector/installation_paths.py'
            ns={'__file__':str(module_path),'__name__':'paths_under_test'}
            exec(compile((ROOT/'raspberry/installation_paths.py').read_text(encoding='utf-8'),str(module_path),'exec'),ns)
            with patch.dict(os.environ,{},clear=True):
                self.assertEqual(ns['installation_root'](),module_path.parent.parent)

    def test_backup_metadata_cli_uses_deployed_custom_root(self):
        with tempfile.TemporaryDirectory() as folder:
            home=Path(folder)/'custom-install';collector=home/'collector';collector.mkdir(parents=True)
            for name in ('installation_paths.py','backup_manifest.py'):
                (collector/name).write_bytes((ROOT/'raspberry'/name).read_bytes())
            daily=home/'backups/daily';daily.mkdir(parents=True)
            (daily/'collector-2026-10-20.sqlite3').write_bytes(b'fictional snapshot for metadata only')
            env=dict(os.environ);env.pop('BOTANEO_HOME',None)
            result=subprocess.run([sys.executable,'-B',str(collector/'backup_manifest.py')],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['name'],'collector-2026-10-20.sqlite3')

    def test_all_service_downloads_are_rendered_before_activation(self):
        for name in ('install_raspberry.sh','update_raspberry.sh'):
            source=(ROOT/'raspberry/install'/name).read_text(encoding='utf-8')
            self.assertIn('download "raspberry/installation_paths.py"',source)
            self.assertEqual(source.count('download "raspberry/$unit"'),source.count('sed -i "s|%h/botaneo|$BOTANEO_HOME|g"'))
