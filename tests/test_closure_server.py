import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from closure_review.__main__ import Handler, explain
from closure_review.engine import template


class ClosureServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, data=None, headers=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type': 'application/json', **(headers or {})}
        conn.request('POST' if data is not None else 'GET', path,
                     json.dumps(data) if data is not None else None, headers)
        response = conn.getresponse()
        status, raw = response.status, response.read()
        conn.close()
        return status, raw

    def test_demo_and_comparison(self):
        status, raw = self.request('/api/demo')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['mode'], 'illustrative')
        status, raw = self.request('/api/compare', {'baseline_csv': template('baseline'), 'current_csv': template('current')})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['comparison']['delta'], 191830)

    def test_invalid_import_and_cross_origin(self):
        status, raw = self.request('/api/compare', {'baseline_csv': '', 'current_csv': ''})
        self.assertEqual(status, 400)
        self.assertIn('error', json.loads(raw))
        status, _ = self.request('/api/compare', {}, {'Origin': 'https://untrusted.example'})
        self.assertEqual(status, 403)
        status, _ = self.request('/api/demo', headers={'Host': 'untrusted.example'})
        self.assertEqual(status, 403)

    def test_unconfigured_ai_explicit(self):
        with patch.dict('os.environ', {}, clear=True):
            status, raw = self.request('/api/explain', {'comparison': {'rows': []}})
        self.assertEqual(status, 503)
        self.assertIn('OPENAI_API_KEY', json.loads(raw)['error'])

    def test_ai_request_preserves_context_and_never_stores_key(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'status':'completed', 'output':[{'type':'message','content':[{'type':'output_text','text':'Review draft'}]}]}).encode()
        with patch.dict('os.environ', {'OPENAI_API_KEY':'test-only-placeholder','ATLASIQ_AI_MODEL':'test-model'}), patch('closure_review.__main__.urlopen', return_value=Response()) as call:
            result = explain({'mode':'illustrative','comparison':{'rows':[]}})
        self.assertEqual(result['text'], 'Review draft')
        payload = json.loads(call.call_args.args[0].data)
        self.assertFalse(payload['store'])
        self.assertEqual(json.loads(payload['input'])['mode'], 'illustrative')
        self.assertNotIn('test-only-placeholder', json.dumps(result))
