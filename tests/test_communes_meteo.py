import sys,unittest
from pathlib import Path
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'_app'))
import communes_meteo as m

class TownTests(unittest.TestCase):
 def test_postcode(self):
  self.assertEqual(m.postcode('92 380'),'92380')
  for code in ('92','380','abc','923800'):
   with self.assertRaises(ValueError):m.postcode(code)
 def test_multiple_towns_and_bad_centres(self):
  data=[{'nom':name,'code':str(index),'codesPostaux':['12345'],'centre':{'coordinates':[2.2,48.8]}} for index,name in enumerate(('Town B','Town A'))]
  data.append({'nom':'Invalid','code':'3','codesPostaux':['12345'],'centre':{'coordinates':[2.2,float('nan')]}})
  self.assertEqual([town['name'] for town in m.normalise(data,'12345')],['Town A','Town B'])
 def test_public_lookup_no_auth(self):
  with patch.object(m.requests,'get',return_value=Mock(status_code=200,content=b'[]',json=lambda:[])) as request:
   self.assertEqual(m.search('92380'),[])
   self.assertEqual(request.call_args.kwargs['params']['codePostal'],'92380')
   self.assertNotIn('headers',request.call_args.kwargs)

if __name__=='__main__':unittest.main()
