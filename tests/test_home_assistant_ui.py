import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
import home_assistant_ui as ui

class ConfigTests(unittest.TestCase):
    def test_no_file_created_on_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            self.assertFalse(ui.load(path)['enabled'])
            self.assertFalse(path.exists())
    def test_draft_and_identity_preserved_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            with patch('requests.Session', side_effect=AssertionError('network')):
                first = ui.save_config('', '', [], path)
                saved = json.loads(path.read_text(encoding='utf-8'))
                saved.update(enabled=True, future_option='keep')
                path.write_text(json.dumps(saved), encoding='utf-8')
                second = ui.save_config('https://example.invalid', 'fictitious-token', [], path)
            self.assertEqual(first['instance_id'], second['instance_id'])
            self.assertFalse(second['enabled'])
            self.assertEqual(second['future_option'], 'keep')
    def test_invalid_config_does_not_replace_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            ui.save_config('', '', [], path)
            before = path.read_bytes()
            for url, token, entities in [('http://public.example', '', []), ('', 'Bearer wrong-prefix', []), ('', '', [{'entity_id': 'sensor.bad'}])]:
                with self.assertRaises(ValueError):
                    ui.save_config(url, token, entities, path)
                self.assertEqual(path.read_bytes(), before)
    def test_invalid_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            path.write_text('broken', encoding='utf-8')
            with self.assertRaises(RuntimeError):
                ui.save_config('', '', [], path)
            self.assertEqual(path.read_text(), 'broken')

if __name__ == '__main__':
    unittest.main()
