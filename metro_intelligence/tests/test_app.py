import io
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from test_analytics import workbook

class AppTests(unittest.TestCase):
 def test_anonymous_locked(self):
  at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
  self.assertFalse(at.exception)
  self.assertTrue(any('locked' in e.value for e in at.error))
 def test_dashboard_and_reviewed_arabic_query(self):
  with patch('security.require_access',return_value='analyst'),patch('streamlit.file_uploader',return_value=io.BytesIO(workbook())):
   at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
   self.assertFalse(at.exception)
   self.assertEqual(len(at.metric),3)
   at.text_input[0].set_value('أعلى 5 فروع مبيعات في طلبات')
   at.button[0].click().run()
   self.assertFalse(at.exception)
   at.button[1].click().run()
   self.assertFalse(at.exception)
   self.assertTrue(any('1,800.00' in e.value for e in at.markdown))
