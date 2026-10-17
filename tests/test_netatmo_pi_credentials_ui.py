import sys,tempfile,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import netatmo_pi_credentials_ui as m

class CredentialTests(unittest.TestCase):
 def test_changed_fields_reset_validation_without_network(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'private.json';path.write_text(json.dumps({'independent_authorization':True,'expires_at':9999999999,'client_id':'old','client_secret':'old','access_token':'old','refresh_token':'old'}))
   self.assertTrue(m.save_fields({field:'fictive' for field in m.FIELDS},path))
   result=json.loads(path.read_text());self.assertFalse(result['independent_authorization']);self.assertEqual(result['expires_at'],0)
 def test_invalid_input_preserves_file(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'private.json';path.write_text('{}');original=path.read_bytes()
   with self.assertRaises(ValueError):m.save_fields({'client_id':'invalid internal space'},path)
   self.assertEqual(path.read_bytes(),original)

if __name__=='__main__':unittest.main()
