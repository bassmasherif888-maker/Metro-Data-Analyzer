import io
import unittest
from unittest.mock import patch
import pandas as pd
from analytics import CHANNELS, REQUIRED, Plan, load_file, parse_question, execute, safe_csv
from security import role_for

def workbook(modifier=None):
 out=io.BytesIO()
 with pd.ExcelWriter(out,engine='openpyxl') as writer:
  for i,sheet in enumerate(CHANNELS):
   rows=[]
   for month in (1,2):
    row={c:'A' for c in REQUIRED}
    row.update(Sales=100*(i+1),Quantity=2,Month=month)
    rows.append(row)
   frame=pd.DataFrame(rows)
   if modifier: frame=modifier(frame)
   frame.to_excel(writer,sheet_name=sheet,index=False)
 return out.getvalue()

class AnalyticsTests(unittest.TestCase):
 def setUp(self): self.ds=load_file(workbook())
 def test_mapping_reconciliation(self):
  self.assertEqual(set(self.ds.data.Channel),{'Instashop','Metro Website','valU','Talabat'})
  self.assertEqual(set(self.ds.data[self.ds.data.Channel=='Talabat']['Channel Detail']),{'Cash via rider','Card in Talabat'})
  self.assertTrue(self.ds.reconciliation.Status.eq('PASS').all())
  self.assertEqual(self.ds.data.Sales.sum(),3000)
 def test_bilingual_query(self):
  for q in ('top 5 branches by sales in Talabat','أعلى 5 فروع مبيعات في طلبات'):
   plan=parse_question(q); result,evidence=execute(self.ds.data,plan)
   self.assertEqual(result.value.sum(),1800); self.assertEqual(evidence['scope_rows'],4)
 def test_month_filter(self):
  r,e=execute(self.ds.data,parse_question('quantity by channel month 2'))
  self.assertEqual(e['scope_rows'],5); self.assertEqual(r.value.sum(),10)
 def test_unsupported(self):
  for q in ('profit by channel','why sales declined','عدد العملاء','orders by month','hello','sales month 15'):
   with self.assertRaises(ValueError): parse_question(q)
 def test_sql_injection(self):
  with self.assertRaises(ValueError): execute(self.ds.data,Plan(dimension='Channel; DROP TABLE facts'))
 def test_incomplete_metrics_blocked(self):
  ds=load_file(workbook(lambda f:f.assign(Sales=['bad',100])))
  self.assertTrue(ds.reconciliation.Status.eq('BLOCKED').all())
  with self.assertRaises(ValueError): execute(ds.data,Plan())
 def test_missing_metric(self):
  with self.assertRaises(ValueError): execute(self.ds.data,Plan(metric='sales_without_tax'))
 def test_invalid_month_and_duplicate_warning(self):
  ds=load_file(workbook(lambda f:pd.concat([f.assign(Month=1.5)]*2,ignore_index=True)))
  self.assertTrue(ds.data.Month.isna().all())
  self.assertTrue(any('repeated' in w for w in ds.warnings))
 def test_missing_columns_fails_closed(self):
  with self.assertRaises(ValueError): load_file(workbook(lambda f:f.drop(columns='Quantity')))
 def test_exports(self):
  self.assertIn("'=HYPERLINK",safe_csv(pd.DataFrame({'name':['=HYPERLINK("x")']})).decode('utf-8-sig'))
 def test_roles(self):
  roles={'person@example.com':'analyst'}
  self.assertIsNone(role_for('person@example.com',False,roles))
  self.assertIsNone(role_for('other@example.com',True,roles))
  self.assertEqual(role_for('PERSON@example.com',True,roles),'analyst')
 def test_evidence(self):
  r,e=execute(self.ds.data,Plan(dimension='month'))
  self.assertEqual(list(r.grouping),[1,2]); self.assertEqual(e['scope_total'],3000)
  self.assertEqual(len(e['source_sheets']),5)
 def test_ai_is_plan_only(self):
  from assistant import ai_plan
  from unittest.mock import Mock
  response=Mock()
  response.json.return_value={'choices':[{'message':{'content':'{"metric":"sales","dimension":"channel","channels":[],"months":[],"limit":10}'}}]}
  with patch('assistant.requests.post',return_value=response) as post:
   plan=ai_plan('sales by channel',{'endpoint':'https://approved.example/chat','api_key':'test','model':'test'})
   self.assertEqual(plan,Plan())
   self.assertNotIn('3000',str(post.call_args))
  response.json.return_value={'choices':[{'message':{'content':'{"sql":"DROP TABLE facts"}'}}]}
  with patch('assistant.requests.post',return_value=response):
   with self.assertRaises(ValueError): ai_plan('x',{'endpoint':'https://approved.example/chat','api_key':'test','model':'test'})

if __name__=='__main__': unittest.main()
