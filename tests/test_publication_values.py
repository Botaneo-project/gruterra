import hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from publication_value_scanner import scan
spec=importlib.util.spec_from_file_location('publication_guard',ROOT/'verifier_avant_github.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)

class PublicationValueTests(unittest.TestCase):
 def test_empty_nested_json_is_allowed(self):
  self.assertEqual(scan(json.dumps({'nested':[{'access_token':'','client_secret':None,'password':'   '}]}),'.json'),set())
 def test_filled_fields_are_blocked(self):
  for key in ('access_token','refresh_token','client_secret','password','private_key','token','application_id'):
   with self.subTest(key=key):self.assertIn('filled_secret_field',scan(json.dumps({key:'fictional-secret'}),'.json'))
 def test_python_empty_fields_and_dynamic_read_are_allowed(self):
  source="access_token = ''\ndata = {'client_secret': None}\ntoken = config.get('access_token')\n"
  self.assertEqual(scan(source,'.py'),set())
 def test_python_assignments_defaults_and_embedded_json_are_checked(self):
  sources=["access_token='fictional-secret'", "cfg['password']='fictional-secret'", "cfg={'private_key':'fictional-secret'}", "def f(access_token='fictional-secret'): pass", "f(access_token='fictional-secret')", "token='fictional'+'-secret'", "text='\"\"'", "text='{\"access_token\":\"fictional-secret\"}'"]
  for source in sources:
   if source=="text='\"\"'":continue
   with self.subTest(source_kind=source.split('=')[0]):self.assertIn('filled_secret_field',scan(source,'.py'))
 def test_docs_and_env_empty_values_allowed_filled_values_blocked(self):
  self.assertEqual(scan('ACCESS_TOKEN=\n"client_secret": ""','.md'),set())
  self.assertIn('filled_secret_field',scan('ACCESS_TOKEN=fictional-secret','.md'))
  self.assertIn('filled_secret_field',scan('"client_secret": "fictional-secret"','.md'))
 def test_hash_exception_expires_after_any_edit(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);path='tests/fake.py';content="access_token='fictional-secret'"
   (root/'publication_fixtures_reviewed.json').write_text(json.dumps({path:hashlib.sha256(content.encode()).hexdigest()}))
   with patch.object(guard,'ROOT',root):
    self.assertEqual(guard.problemes_valeurs(path,content),set())
    self.assertEqual(guard.problemes_valeurs(path,content+'\n'),{'filled_secret_field'})
 def test_recognizable_secret_is_never_waived_even_with_matching_hash(self):
  value='ghp_'+'a'*32
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);path='README.md';content='x'*510000+value
   (root/path).write_text(content)
   (root/'publication_fixtures_reviewed.json').write_text(json.dumps({path:hashlib.sha256(content.encode()).hexdigest()}))
   with patch.object(guard,'ROOT',root):
    result=guard.verifier_contenu_secret([path])
    self.assertEqual(len(result),1);self.assertNotIn(value,result[0])
 def test_empty_private_configuration_still_blocked_by_path(self):
  self.assertTrue(guard.est_sensible('_config/profile.json'))
  self.assertTrue(guard.est_sensible('profile.local.json'))
 def test_source_and_json_templates_are_value_checked_not_filename_whitelisted(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'credentials.py';template=root/'oauth.json.example'
   with patch.object(guard,'ROOT',root):
    source.write_text("access_token=''\n");template.write_text('{"access_token":""}')
    self.assertFalse(guard.est_sensible(source.name));self.assertFalse(guard.est_sensible(template.name))
    source.write_text("access_token='fictional-secret'\n");template.write_text('{"access_token":"fictional-secret"}')
    self.assertTrue(guard.est_sensible(source.name));self.assertTrue(guard.est_sensible(template.name))
 def test_invalid_structured_files_fail_closed(self):
  self.assertEqual(scan('{"access_token":','.json'),{'unreadable_json'})
  self.assertEqual(scan('access_token = ','.py'),{'unreadable_python'})
