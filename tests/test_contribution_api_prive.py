import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

RUNNER=Path(__file__).resolve().parents[1]/'tools/essai_contribution_api_prive.py'
spec=importlib.util.spec_from_file_location('private_runner',RUNNER)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class PrivateAPITests(unittest.TestCase):
    def test_complete_simulation_uses_application_modules_without_user_config(self):
        with tempfile.TemporaryDirectory() as folder:
            sentinel=Path(folder)/'contribution.identity.local.json'
            sentinel.write_text('PRIVATE SENTINEL',encoding='utf-8')
            env=dict(os.environ,BOTANEO_CONFIG_DIR=folder,BOTANEO_DEMO='1')
            result=subprocess.run([sys.executable,'-X','utf8',str(RUNNER)],env=env,capture_output=True,text=True,encoding='utf-8',timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('SIMULATION LOCALE',result.stdout)
            self.assertIn('Reprise 200',result.stdout)
            self.assertIn('Nettoyage fictif confirmé',result.stdout)
            self.assertEqual(sentinel.read_text(encoding='utf-8'),'PRIVATE SENTINEL')
            self.assertEqual(list(Path(folder).iterdir()),[sentinel])

    def test_import_creates_no_application_identity_or_network_request(self):
        self.assertNotIn('contribution_identite',runner.__dict__)
        self.assertNotIn('contribution_suivi',runner.__dict__)

    def test_transport_refuses_redirects_and_unknown_endpoints(self):
        with self.assertRaises(ValueError):runner.NoRedirect().redirect_request(None,None,None,None,None,None)
        transport=runner.PrivateTransport('fictional-test-token')
        with patch.object(transport._opener,'open',side_effect=AssertionError('No network allowed')):
            for path in ('http://api.gruterra.fr/v2/challenges','/v2/unknown','https://evil.invalid','/v2/challenges?redirect=1'):
                with self.assertRaises(ValueError):transport(path,{})

    def test_response_limits_duplicate_keys_invalid_utf8_and_non_objects(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'[]',b'\xff',b' '* (runner.LIMIT+1)):
            with self.assertRaises((ValueError,UnicodeError)):runner.decode_response(raw)
        self.assertEqual(runner.decode_response(b'{"error":"contribution_expired"}'),{'error':'contribution_expired'})


    def test_diagnostic_suppresses_unknown_error_and_raw_exception(self):
        import io
        from contextlib import redirect_stdout
        output=io.StringIO()
        with redirect_stdout(output):
            diagnostic=runner.Diagnostic()
            diagnostic.enter('Première contribution')
            diagnostic.response(401,{'error':'unauthorized','token':'DO_NOT_PRINT'})
            diagnostic.failed(ValueError('RAW_EXCEPTION_SECRET'))
            diagnostic.response(503,{'error':'SERVER_SECRET_DO_NOT_PRINT'})
        text=output.getvalue()
        self.assertIn('HTTP : 401',text)
        self.assertIn('unauthorized',text)
        self.assertIn('non reconnu',text)
        self.assertNotIn('DO_NOT_PRINT',text)
        self.assertNotIn('RAW_EXCEPTION',text)

    def test_simulated_failure_prints_prior_successes_and_original_failure_before_cleanup(self):
        # Fresh child process keeps production modules isolated exactly as the launcher.
        code="""
import importlib.util,sys
spec=importlib.util.spec_from_file_location('runner',sys.argv[1])
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
original=r.SimulatedAPI.__call__
def failure(self,path,body):
    if path in ('/v2/contributions','/v2/withdrawals') and self.receipts:
        return 503,{'error':'storage_unavailable','secret':'SENTINEL_PRIVATE_CONTENT'}
    return original(self,path,body)
r.SimulatedAPI.__call__=failure
sys.argv=[sys.argv[1]]
raise SystemExit(r.main())
"""
        result=subprocess.run([sys.executable,'-X','utf8','-c',code,str(RUNNER)],capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(result.returncode,1)
        self.assertIn('OK : Réception 201',result.stdout)
        self.assertIn('ÉCHEC · étape : Reprise de la première contribution',result.stdout)
        self.assertIn('HTTP : 503 · code serveur : storage_unavailable',result.stdout)
        self.assertIn('NETTOYAGE NON CONFIRMÉ',result.stdout)
        self.assertLess(result.stdout.index('OK : Réception'),result.stdout.index('ÉCHEC ·'))
        self.assertNotIn('SENTINEL_PRIVATE_CONTENT',result.stdout+result.stderr)
        self.assertNotIn('Traceback',result.stdout+result.stderr)

    def test_malformed_http_body_keeps_status_without_disclosing_content(self):
        from io import BytesIO
        class Response(BytesIO):
            code=502
            def geturl(self):return runner.ORIGIN+'/v2/challenges'
        transport=runner.PrivateTransport('FICTIONAL_PRIVATE_TOKEN')
        with patch.object(transport._opener,'open',return_value=Response(b'PRIVATE_HTML_SECRET')):
            with self.assertRaises(runner.SafeTransportError) as caught:transport('/v2/challenges',{})
        self.assertEqual(caught.exception.status,502)
        self.assertNotIn('PRIVATE',str(caught.exception))
