import sys,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import meteofrance_oauth as m

class OAuthTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'profile.json'
  self.now=datetime(2026,10,12,20,tzinfo=timezone.utc)
  self.config={'auth_mode':'oauth2','application_id':'fictive','access_token':'old','expires_at_utc':'2026-10-12T19:00:00Z'}
  self.path.write_text(json.dumps(self.config),encoding='utf-8')
 def test_generate_then_reuse_without_second_request(self):
  request=Mock(return_value=Mock(status_code=200,json=lambda:{'access_token':'fictional-token','expires_in':3600,'token_type':'Bearer'}))
  self.assertEqual(m.access_token(self.path,request,self.now),'fictional-token')
  self.assertEqual(m.access_token(self.path,request,self.now),'fictional-token');request.assert_called_once()
  config=json.loads(self.path.read_text());self.assertEqual(config['application_id'],'fictive');self.assertEqual(config['expires_at_utc'],'2026-10-12T21:00:00Z')
  self.assertFalse(request.call_args.kwargs['allow_redirects'])
 def test_refusal_preserves_profile_and_no_retry(self):
  original=self.path.read_bytes();request=Mock(return_value=Mock(status_code=401))
  with self.assertRaisesRegex(RuntimeError,'mf_oauth_http_401'):m.access_token(self.path,request,self.now)
  self.assertEqual(self.path.read_bytes(),original);request.assert_called_once()
 def test_network_exception_is_sanitized(self):
  request=Mock(side_effect=RuntimeError('PRIVATE_SECRET'))
  with self.assertRaisesRegex(RuntimeError,'^mf_oauth_network_error$'):m.access_token(self.path,request,self.now)
 def test_manual_mode_no_generation_or_lock(self):
  self.config['auth_mode']='bearer';self.path.write_text(json.dumps(self.config));request=Mock()
  with self.assertRaisesRegex(RuntimeError,'mf_oauth_not_enabled'):m.access_token(self.path,request,self.now)
  request.assert_not_called();self.assertFalse(Path(str(self.path)+'.lock').exists())
 def test_invalid_response_preserves_profile(self):
  original=self.path.read_bytes();request=Mock(return_value=Mock(status_code=200,json=lambda:{'access_token':'x','expires_in':True,'token_type':'Bearer'}))
  with self.assertRaisesRegex(RuntimeError,'mf_oauth_response_invalid'):m.access_token(self.path,request,self.now)
  self.assertEqual(self.path.read_bytes(),original)

if __name__=='__main__':unittest.main()
