"""Essais Windows isolés : aucun réseau, pip ou donnée utilisateur."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
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

    def bootstrap_harness(self,install_succeeds):
        source=(ROOT/'Installer_Gruterra.bat').read_text(encoding='utf-8-sig')
        prefix=source.split("echo [2/6]",1)[0]
        expected=self.root/'newly installed Python/Scripts/python.exe'
        prefix=prefix.replace('set "PYTHON_EXPECTED_EXE=%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe"','set "PYTHON_EXPECTED_EXE='+str(expected)+'"')
        detection=source.split('\n:detect_python\n',1)[1].split('\n:install_python\n',1)[0]
        # The real detector runs with an empty PATH. Only the OS installation
        # step is replaced; a genuine temporary interpreter is created.
        install=('"'+sys.executable+'" -m venv --without-pip "'+str(expected.parent.parent)+'"\nexit /b %errorlevel%\n') if install_succeeds else 'exit /b 1\n'
        harness=self.root/'bootstrap.bat'
        harness.write_text(prefix+'echo BOOTSTRAP_CONTINUED\nexit /b 0\n:detect_python\n'+detection+'\n:install_python\n'+install+'\n:python_missing\nexit /b 1\n:fail\nexit /b 1\n',encoding='utf-8')
        env=os.environ.copy();env['PATH']=''
        return self.execute(harness,env)

    def test_missing_python_installation_then_redetection_continues(self):
        result=self.bootstrap_harness(True)
        self.assertEqual(result.returncode,0)
        self.assertIn('BOOTSTRAP_CONTINUED',result.stdout)

    def test_missing_python_failed_installation_stops(self):
        # Ensure this scenario starts without the temporary installed Python.
        installed=self.root/'newly installed Python'
        if installed.exists():shutil.rmtree(installed)
        result=self.bootstrap_harness(False)
        self.assertEqual(result.returncode,1)
        self.assertNotIn('BOOTSTRAP_CONTINUED',result.stdout)

    def test_exact_installed_python_has_priority_over_path_probes(self):
        source=(ROOT/'Installer_Gruterra.bat').read_text(encoding='utf-8-sig')
        routine=source.split('\n:detect_python\n',1)[1].split('\n:install_python\n',1)[0]
        # Tripwires prove no PATH probe runs before the valid exact interpreter.
        routine=routine.replace('where py >nul 2>nul','exit /b 91').replace('where python >nul 2>nul','exit /b 92')
        harness=self.root/'priority.bat'
        harness.write_text('@echo off\nset "PYTHON_EXPECTED_EXE='+str(self.root/'.venv/Scripts/python.exe')+'"\ncall :detect_python\nexit /b %errorlevel%\n:detect_python\n'+routine,encoding='utf-8')
        result=self.execute(harness)
        self.assertEqual(result.returncode,0)
