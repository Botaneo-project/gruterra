from contextlib import closing
from datetime import datetime, timedelta
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
import creer_base_demo as demo
import lamp_sync

class DemoLightingTests(unittest.TestCase):
    def test_demo_generator_uses_only_fictional_rows_and_private_demo_schedule(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            db_path = folder/'demo.db'
            with patch.object(demo, 'DEMO_DIR', folder), patch.object(demo, 'DEMO_DB', db_path), patch.object(demo, 'SOURCE_DB', folder/'missing-real.db'):
                demo.creer_base_demo()
            with closing(sqlite3.connect(db_path)) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM plantes').fetchone()[0], 4)
                self.assertEqual(db.execute("SELECT count(*) FROM mesures WHERE donnees_brutes!='demo'").fetchone()[0], 0)
                self.assertGreater(db.execute('SELECT count(*) FROM mesures WHERE luminosite=0').fetchone()[0], 0)
                missing_day = (datetime.now()-timedelta(days=2)).date().isoformat()
                self.assertEqual(db.execute('SELECT count(*) FROM mesures WHERE capteur_id=1 AND date_heure LIKE ?', (missing_day+'T11:%',)).fetchone()[0], 0)
            self.assertTrue((folder/'config/light-schedules.json').is_file())
    def test_demo_sync_does_not_read_raspberry_config(self):
        with patch.dict(os.environ, {'BOTANEO_DEMO': '1'}), patch('tkinter.messagebox.showinfo') as info, patch('suivi_raspberry.load_config', side_effect=AssertionError('real config')):
            lamp_sync.resolve_window(None, 1)
            info.assert_called_once()
    def test_demo_paths_follow_config_environment_in_fresh_process(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory)/'demo-config'
            code = "import sys;sys.path.insert(0,sys.argv[1]);import light_window_ui,lamp_sync;from pathlib import Path;assert light_window_ui.CONFIG==Path(sys.argv[2])/'light-schedules.json';assert lamp_sync.ROOT==Path(sys.argv[2])"
            env = {**os.environ, 'BOTANEO_DEMO': '1', 'BOTANEO_CONFIG_DIR': str(config)}
            result = subprocess.run([sys.executable, '-B', '-c', code, str(Path(demo.__file__).parent), str(config)], env=env, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, 'Demo paths must use the isolated config directory')

if __name__ == '__main__':
    unittest.main()
