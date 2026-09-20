import json
import tempfile
import unittest
from pathlib import Path
from sync_export import collect_now

class CollectNowTests(unittest.TestCase):
    def test_queue_and_duplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base/'data').mkdir()
            (base/'data/collect-state.json').write_text(json.dumps({'running': False}))
            self.assertTrue(collect_now(base, {})['accepted'])
            self.assertEqual(collect_now(base, {})['status'], 'pending')
            self.assertFalse(collect_now(base, {})['accepted'])

    def test_running_does_not_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base/'data').mkdir()
            (base/'data/collect-state.json').write_text(json.dumps({'running': True}))
            self.assertEqual(collect_now(base, {})['status'], 'running')
            self.assertFalse((base/'data/collect.request').exists())

    def test_invalid_request(self):
        with self.assertRaises(ValueError):
            collect_now(Path('.'), [])

if __name__ == '__main__':
    unittest.main()
