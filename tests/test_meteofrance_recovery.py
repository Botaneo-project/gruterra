import sys,unittest
from pathlib import Path
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import meteofrance_oauth as m

class RecoveryTests(unittest.TestCase):
 def test_one_refresh_after_401(self):
  request=Mock(side_effect=[Mock(status_code=401),Mock(status_code=200)])
  with patch.object(m,'access_token',side_effect=['first','second']) as token:
   result=m.authorized_get('fictive','https://public-api.meteofrance.fr/public/aromepi/1.0/test',requester=request)
  self.assertEqual(result.status_code,200);self.assertEqual(token.call_count,2);self.assertTrue(token.call_args.kwargs['force_refresh']);self.assertEqual(request.call_count,2)
 def test_second_401_no_loop(self):
  request=Mock(return_value=Mock(status_code=401))
  with patch.object(m,'access_token',return_value='fictive'):
   self.assertEqual(m.authorized_get('fictive','https://public-api.meteofrance.fr/public/test',requester=request).status_code,401)
  self.assertEqual(request.call_count,2)
 def test_other_host_rejected_before_auth(self):
  with patch.object(m,'access_token') as token:
   for url in ('http://public-api.meteofrance.fr/public/test','https://example.com/public/test','https://public-api.meteofrance.fr@other.invalid/public/test'):
    with self.assertRaises(ValueError):m.authorized_get('fictive',url)
   token.assert_not_called()

if __name__=='__main__':unittest.main()
