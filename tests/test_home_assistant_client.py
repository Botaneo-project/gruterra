import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_app'))
from home_assistant_client import read_snapshot

class Response:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self.body = body or b'{}'
        self.closed = False
    def iter_content(self, chunk_size):
        yield self.body
    def close(self):
        self.closed = True

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.config = {'schema_version': 1, 'enabled': True, 'base_url': 'http://127.0.0.1:8123', 'access_token': 'fictitious-token', 'instance_id': 'fictitious-ha', 'entities': [{'entity_id': 'sensor.test_lux', 'device_id': 'fictitious-device', 'model': 'fictitious-model', 'metric': 'illuminance'}]}
        self.time = '2026-10-15T10:00:00Z'
        self.state = {'entity_id': 'sensor.test_lux', 'state': '0', 'attributes': {'unit_of_measurement': 'lx'}, 'last_updated': self.time}
    def call(self, config=None, requester=None):
        return read_snapshot(self.config if config is None else config, received_at=self.time, requester=requester)
    def test_disabled_has_no_network(self):
        self.assertEqual(self.call({**self.config, 'enabled': False}, lambda *a, **k: self.fail('network'))['code'], 'disabled')
    def test_only_selected_entity_read_and_response_closed(self):
        response = Response(body=json.dumps(self.state).encode())
        calls = []
        def fake(url, **kwargs):
            calls.append((url, kwargs))
            return response
        result = self.call(requester=fake)
        self.assertTrue(result['ok'])
        self.assertEqual(result['records'][0]['value'], '0')
        self.assertEqual(calls[0][0], 'http://127.0.0.1:8123/api/states/sensor.test_lux')
        self.assertFalse(calls[0][1]['allow_redirects'])
        self.assertTrue(response.closed)
    def test_errors_safe_no_retry_or_partial_success(self):
        for status, code in [(401, 'unauthorized'), (403, 'forbidden'), (404, 'entity_not_found'), (429, 'rate_limited'), (302, 'http_error')]:
            count = []
            response = Response(status, b'secret-body')
            def fake(*args, **kwargs):
                count.append(1)
                return response
            result = self.call(requester=fake)
            self.assertEqual(result['code'], code)
            self.assertEqual(result['records'], [])
            self.assertEqual(len(count), 1)
            self.assertNotIn('secret', str(result))
            self.assertTrue(response.closed)
    def test_invalid_config_never_contacts_server(self):
        for change in [{'base_url': 'http://public.example'}, {'base_url': 'https://user:password@example.org'}, {'base_url': 'https://example.org/?token=x'}, {'entities': self.config['entities'] * 2}, {'entities': [{**self.config['entities'][0], 'metric': 'bad'}]}]:
            result = self.call({**self.config, **change}, lambda *a, **k: self.fail('network'))
            self.assertFalse(result['ok'])
    def test_malformed_oversized_and_secret_exception(self):
        for body in [b'x', b'{"state":"1","state":"2"}', b'x'*65537]:
            self.assertFalse(self.call(requester=lambda *a, **k: Response(body=body))['ok'])
        def fail(*args, **kwargs):
            raise RuntimeError('secret token and private host')
        self.assertEqual(self.call(requester=fail), {'ok': False, 'code': 'connection_failed', 'http_status': None, 'records': []})
    def test_failure_after_first_entity_discards_partial_snapshot(self):
        config = copy.deepcopy(self.config)
        config['entities'].append({**config['entities'][0], 'entity_id': 'sensor.other'})
        responses = iter([Response(body=json.dumps(self.state).encode()), Response(404)])
        result = self.call(config, lambda *a, **k: next(responses))
        self.assertFalse(result['ok'])
        self.assertEqual(result['records'], [])

if __name__ == '__main__':
    unittest.main()
