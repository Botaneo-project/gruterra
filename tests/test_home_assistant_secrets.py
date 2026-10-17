import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
import home_assistant_secrets as secret
import home_assistant_ui as ui

@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI tests')
class SecretTests(unittest.TestCase):
    def test_dpapi_roundtrip_and_no_plaintext_on_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            ui.save_config('https://example.invalid', 'fictitious-private-token', [], path)
            self.assertNotIn('fictitious-private-token', path.read_text())
            self.assertNotIn('access_token', json.loads(path.read_text()))
            self.assertEqual(ui.load(path)['access_token'], 'fictitious-private-token')
    def test_legacy_migrates_and_preserves_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            path.write_text(json.dumps({'schema_version': 1, 'enabled': False, 'entities': [], 'instance_id': 'existing-ha', 'access_token': 'legacy-fictitious-token'}))
            data = ui.load(path)
            self.assertEqual(data['instance_id'], 'existing-ha')
            self.assertEqual(data['access_token'], 'legacy-fictitious-token')
            self.assertNotIn('legacy-fictitious-token', path.read_text())
    def test_failure_preserves_old_file_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            ui.save_config('', 'old-fictitious-token', [], path)
            before = path.read_bytes()
            with patch.object(secret, 'protect', side_effect=ValueError('secure_storage_unavailable')):
                with self.assertRaises(ValueError):
                    ui.save_config('', 'new-fictitious-token', [], path)
            self.assertEqual(path.read_bytes(), before)
    def test_unreadable_secret_can_be_replaced_but_not_silently_erased(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            ui.save_config('', 'fictitious-token', [], path)
            data = json.loads(path.read_text())
            data['access_token_protected'] = 'invalid-blob'
            path.write_text(json.dumps(data))
            before = path.read_bytes()
            self.assertTrue(ui.load(path)['_secret_unavailable'])
            with self.assertRaises(ValueError):
                ui.save_config('', '', [], path)
            self.assertEqual(path.read_bytes(), before)
            ui.save_config('', 'replacement-fictitious-token', [], path)
            self.assertEqual(ui.load(path)['access_token'], 'replacement-fictitious-token')

if __name__ == '__main__':
    unittest.main()
