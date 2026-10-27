import unittest
from unittest.mock import Mock, patch
from security import local_access_allowed, require_access

class LocalTests(unittest.TestCase):
 def test_personal_loopback_allowed(self):
  self.assertTrue(local_access_allowed('1','personal','127.0.0.1','127.0.0.1'))
 def test_nonlocal_and_team_denied(self):
  for values in [('1','team','127.0.0.1','127.0.0.1'),('1','personal','0.0.0.0','127.0.0.1'),('1','personal','127.0.0.1','10.0.0.1'),('0','personal','127.0.0.1','127.0.0.1'),('1','personal','127.0.0.1',None)]:
   self.assertFalse(local_access_allowed(*values))
 def test_personal_gate(self):
  st=Mock(); st.get_option.return_value='127.0.0.1'; st.context.ip_address='127.0.0.1'
  with patch.dict('os.environ',{'METRO_LOCAL_MODE':'1','METRO_DEPLOYMENT':'personal'}):
   self.assertEqual(require_access(st),'analyst')
 def test_team_bypass_stops(self):
  st=Mock(); st.stop.side_effect=RuntimeError('blocked')
  st.get_option.return_value='127.0.0.1'; st.context.ip_address='127.0.0.1'
  with patch.dict('os.environ',{'METRO_LOCAL_MODE':'1','METRO_DEPLOYMENT':'team'}):
   with self.assertRaisesRegex(RuntimeError,'blocked'): require_access(st)
