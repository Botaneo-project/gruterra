"""Essais Windows isolés : aucun réseau, pip ou donnée utilisateur."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import venv

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.name=='nt','Windows BAT launchers')
class WindowsLauncherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='gruterra test paths with spaces ')
        cls.root=Path(cls.temp.name)
        venv.EnvBuilder(with_pip=False).create(cls.root/'.venv')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def execute(self,path,env=None):
        return subprocess.run([os.environ['COMSPEC'],'/d','/c',str(path)],
            cwd=self.root,env=env,input='\n\n',capture_output=True,text=True,
            timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)

    def test_redetect_installed_python_with_spaces_without_path(self):
        source=(ROOT/'Installer_Gruterra.bat').read_text(encoding='utf-8-sig')
        routine=source.split('\n:detect_python\n',1)[1].split('\n:install_python',1)[0]
        harness=self.root/'redetect.bat'
        harness.write_text('@echo off\nset "PYTHON_CMD="\nset "PYTHON_EXPECTED_EXE='+
            str(self.root/'.venv/Scripts/python.exe')+'"\ncall :detect_python\n'+
            'if errorlevel 1 exit /b 7\n%PYTHON_CMD% -c "print(1234567)"\n'+
            'exit /b %errorlevel%\n:detect_python\n'+routine,encoding='ascii')
        env=os.environ.copy();env['PATH']=''
        result=self.execute(harness,env)
        self.assertEqual(result.returncode,0)
        self.assertIn('1234567',result.stdout)

    def test_demo_bat_launches_expected_script_and_propagates_failure(self):
        launcher=self.root/'Lancer_Demo.bat'
        shutil.copyfile(ROOT/'Lancer_Demo.bat',launcher)
        target=self.root/'Lancer_Demo.py'
        marker=self.root/'demo-launch-marker.txt'
        target.write_text("from pathlib import Path\nPath('demo-launch-marker.txt').write_text('ok')\n",encoding='ascii')
        result=self.execute(launcher)
        self.assertEqual(result.returncode,0)
        self.assertEqual(marker.read_text(),'ok')
        marker.unlink()
        target.write_text('raise SystemExit(9)\n',encoding='ascii')
        result=self.execute(launcher)
        self.assertEqual(result.returncode,1)
        self.assertFalse(marker.exists())
