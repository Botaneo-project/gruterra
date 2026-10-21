import importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import prepare_windows_installer as installer
class InstallerBuildGuardTests(unittest.TestCase):
 def test_database_in_selection_blocks_before_output_or_compilation(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'_app').mkdir();(root/'_app/plantes.db').write_bytes(b'fictional')
   compiler=root/'compiler.exe';compiler.write_bytes(b'not executed');output=root/'output'
   with patch.object(installer,'ROOT',root),patch.object(installer.release,'RACINE',root),patch.object(installer.release,'lister_fichiers_suivis',return_value=[Path('_app/plantes.db')]),patch.object(installer.subprocess,'run',side_effect=AssertionError('compiler should not run')):
    with self.assertRaises(RuntimeError):installer.build(compiler,output)
   self.assertFalse(output.exists())
 def test_unknown_private_value_blocks_build_selection(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source=root/'public.json';source.write_text('{"access_token":"fictional-filled-value"}')
   with patch.object(installer.release,'RACINE',root),patch.object(installer.guard,'ROOT',root),patch.object(installer.release,'lister_fichiers_suivis',return_value=[Path('public.json')]):
    with self.assertRaisesRegex(RuntimeError,'Public-source validation failed'):installer.checked_files()
