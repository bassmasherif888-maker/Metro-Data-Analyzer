import io
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from streamlit.testing.v1 import AppTest
from security import require_access
from test_analytics import workbook

APP=str(Path(__file__).resolve().parents[1] / 'public_app.py')

class PublicTests(unittest.TestCase):
 def test_no_signin_needed(self):
  with patch.dict('os.environ',{'METRO_DEPLOYMENT':'public'}):
   at=AppTest.from_file(APP).run()
   self.assertFalse(at.exception)
   self.assertFalse(at.error)
   self.assertTrue(any('نسخة عامة' in item.value for item in at.warning))
 def test_public_workbook_queries(self):
  with patch.dict('os.environ',{'METRO_DEPLOYMENT':'public'}),patch('streamlit.file_uploader',return_value=io.BytesIO(workbook())):
   at=AppTest.from_file(APP).run()
   self.assertFalse(at.exception)
   self.assertEqual(len(at.metric),3)
   at.text_input[0].set_value('top 5 branches by sales in Talabat')
   at.button[0].click().run()
   at.button[1].click().run()
   self.assertFalse(at.exception)
   self.assertTrue(any('1,800.00' in e.value for e in at.markdown))
 def test_public_cannot_override_team(self):
  st=Mock(); st.stop.side_effect=RuntimeError('blocked')
  with patch.dict('os.environ',{'METRO_DEPLOYMENT':'team'}):
   with self.assertRaisesRegex(RuntimeError,'blocked'): require_access(st,public=True)
