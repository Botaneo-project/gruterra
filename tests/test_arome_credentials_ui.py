import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import arome_credentials_ui as m

class FormTests(unittest.TestCase):
 def test_save_oauth_preserves_other_fields(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'private.json';path.write_text(json.dumps({'enabled':False,'auth_mode':'bearer','access_token':'old','expires_at_utc':'2026-10-13T21:00:00Z'}))
   m.save_credentials('oauth2','fictional-id','',path);data=json.loads(path.read_text());self.assertFalse(data['enabled']);self.assertEqual(data['auth_mode'],'oauth2');self.assertIsNone(data['expires_at_utc'])
 def test_reject_missing_or_prefixed_values(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'private.json'
   for mode,application,token in [('oauth2','',''),('bearer','',''),('oauth2','Basic value','')]:
    with self.assertRaises(ValueError):m.save_credentials(mode,application,token,path)
   self.assertFalse(path.exists())

if __name__=='__main__':unittest.main()
