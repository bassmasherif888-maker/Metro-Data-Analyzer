"""Governed SIAM ingestion and read-only analytics; never execute user SQL."""
import hashlib
import io
import re
import sqlite3
import zipfile
from dataclasses import dataclass, asdict
import pandas as pd

CHANNELS = {'Insta': ('Instashop', 'App'), 'Online Metro': ('Metro Website', 'Website'),
 'Online Value': ('valU', 'In-app store'), 'طلبات كاشير مترو ': ('Talabat', 'Cash via rider'),
 'طلبات اون لاين مترو': ('Talabat', 'Card in Talabat')}
REQUIRED = ['Sales','Quantity','Month','Site','Site Description','Department','Category','Sub Category','Article','Article Description']
DIMENSIONS = {'channel':'Channel','month':'Month','branch':'Site Description','department':'Department','category':'Category','product':'Article Description','payment':'Channel Detail'}
METRICS = {'sales':'Sales','quantity':'Quantity','sales_without_tax':'Sales WO Tax'}

@dataclass
class Dataset:
 data: pd.DataFrame
 warnings: list
 reconciliation: pd.DataFrame
 fingerprint: str

def load_file(raw):
 if len(raw) > 200*1024*1024: raise ValueError('Workbook exceeds 200 MiB limit')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if sum(i.file_size for i in z.infolist()) > 1500*1024*1024: raise ValueError('Expanded workbook exceeds safety limit')
 frames=[]; warnings=[]; ledger=[]
 with pd.ExcelFile(io.BytesIO(raw), engine='openpyxl') as xl:
  for sheet in xl.sheet_names:
   if sheet not in CHANNELS:
    warnings.append(f'Excluded unrecognized sheet: {sheet}'); continue
   source=pd.read_excel(xl,sheet_name=sheet)
   missing=set(REQUIRED)-set(source.columns)
   if missing:
    raise ValueError(f'{sheet}: required columns missing: {sorted(missing)}; ingestion stopped to avoid partial totals')
   df=source.copy()
   for col in ['Sales','Quantity','Sales WO Tax']:
    if col in df:
     df[col]=pd.to_numeric(df[col],errors='coerce')
     invalid=df[col].isna() | ~df[col].abs().lt(float('inf'))
     if invalid.any(): warnings.append(f'{sheet}: {int(invalid.sum())} invalid/missing {col}; metric blocked until corrected')
     df.loc[invalid,col]=float('nan')
   month=pd.to_numeric(df.Month,errors='coerce')
   valid_month=month.between(1,12)&month.mod(1).eq(0)
   if not valid_month.all(): warnings.append(f'{sheet}: {int((~valid_month).sum())} invalid months; time-filtered answers exclude these rows')
   df['Month']=month.where(valid_month).astype('Int64')
   for col in ['Site Description','Department','Category','Article Description']:
    if df[col].isna().any(): warnings.append(f'{sheet}: missing {col}; shown as Unknown')
    df[col]=df[col].fillna('Unknown').astype(str)
   duplicates=int(source.duplicated().sum())
   if duplicates: warnings.append(f'{sheet}: {duplicates} repeated rows retained; confirm source grain before deduplicating')
   if df.Sales.lt(0).any(): warnings.append(f'{sheet}: negative sales retained; may represent returns or corrections')
   df['Channel'],df['Channel Detail']=CHANNELS[sheet]
   df['Source Sheet']=sheet; df['Source Row']=range(2,len(df)+2)
   frames.append(df)
   ledger.append({'Sheet':sheet,'Source rows':len(source),'Loaded rows':len(df),
    'Source sales':pd.to_numeric(source.Sales,errors='coerce').sum(min_count=1),
    'Loaded sales':df.Sales.sum(min_count=1),'Invalid sales':int(df.Sales.isna().sum())})
 if not frames: raise ValueError('No recognized SIAM sheets')
 absent=set(CHANNELS)-set(x['Sheet'] for x in ledger)
 if absent: warnings.append('Missing mapped sheets: '+', '.join(sorted(absent)))
 data=pd.concat(frames,ignore_index=True)
 ledger=pd.DataFrame(ledger)
 ledger['Difference']=ledger['Loaded sales']-ledger['Source sales']
 ledger['Status']=ledger.apply(lambda r:'PASS' if r['Invalid sales']==0 and abs(r.Difference)<0.005 and r['Source rows']==r['Loaded rows'] else 'BLOCKED',axis=1)
 warnings.append('Reconciliation compares imported rows with source-sheet numeric totals; no independent finance control total was supplied.')
 return Dataset(data,warnings,ledger,hashlib.sha256(raw).hexdigest())

@dataclass(frozen=True)
class Plan:
 metric: str='sales'
 dimension: str='channel'
 channels: tuple=()
 months: tuple=()
 limit: int=10

def validate(plan):
 if plan.metric not in METRICS or plan.dimension not in DIMENSIONS: raise ValueError('Unsupported metric or grouping')
 if any(c not in {v[0] for v in CHANNELS.values()} for c in plan.channels): raise ValueError('Unknown channel')
 if any(type(m) is not int or not 1<=m<=12 for m in plan.months): raise ValueError('Invalid month')
 if type(plan.limit) is not int or not 1<=plan.limit<=50: raise ValueError('Limit must be 1–50')

def parse_question(question):
 q=question.lower().strip()
 if not q or len(q)>1000: raise ValueError('Enter a question of 1–1000 characters')
 if any(w in q for w in ['profit','margin','aov','order','customer','conversion','forecast','why','سبب','لماذا','ربح','هامش','عميل','عملاء','سلة','توقع','تحويل']):
  raise ValueError('This question needs unavailable order/customer/cost data or causal evidence. Ask about recorded sales, quantity, or sales without tax.')
 if not any(w in q for w in ['sales','quantity','sold','top','trend','مبيعات','بيع','كمية','كميات','اعلى','أعلى','اتجاه']):
  raise ValueError('Please specify sales or quantity, a grouping, and optional channel/month filters.')
 aliases={'Talabat':['talabat','طلبات'],'Instashop':['insta','انستا'],'valU':['valu','value','فاليو'],'Metro Website':['metro website','online metro','موقع مترو']}
 channels=tuple(ch for ch, words in aliases.items() if any(w in q for w in words))
 dimension='channel'
 for dim,words in [('branch',['branch','فروع','فرع']),('product',['product','article','منتج','منتجات']),('department',['department','قسم','أقسام']),('category',['category','فئة','تصنيف']),('payment',['payment','دفع']),('month',['monthly','trend','شهري','شهرية','اتجاه'])]:
  if any(w in q for w in words): dimension=dim; break
 months=tuple(int(m) for m in re.findall(r'(?:month|شهر)\s+(\d{1,2})\b',q))
 match=re.search(r'(?:top|أعلى|اعلى)\s+(\d{1,2})',q)
 metric='quantity' if any(w in q for w in ['quantity','كمية','كميات']) else 'sales_without_tax' if any(w in q for w in ['without tax','بدون ضريبة']) else 'sales'
 plan=Plan(metric,dimension,channels,months,int(match.group(1)) if match else 10)
 validate(plan); return plan

def execute(data,plan):
 validate(plan)
 subset=data
 if plan.channels: subset=subset[subset.Channel.isin(plan.channels)]
 if plan.months: subset=subset[subset.Month.isin(plan.months)]
 col=METRICS[plan.metric]; dim=DIMENSIONS[plan.dimension]
 if subset.empty: raise ValueError('No rows match the selected scope')
 if col not in subset or subset[col].isna().any(): raise ValueError(f'{col} is missing or incomplete in this scope; no total reported')
 # Only identifiers from fixed allowlists enter SQL. Values always use parameters.
 sql=f'SELECT "{dim}" AS grouping, SUM("{col}") AS value, COUNT(*) AS source_rows FROM facts GROUP BY "{dim}" ORDER BY '+('grouping ASC' if plan.dimension=='month' else 'value DESC, grouping ASC')+' LIMIT ?'
 with sqlite3.connect(':memory:') as conn:
  subset[[dim,col]].to_sql('facts',conn,index=False)
  conn.execute('PRAGMA query_only = ON')
  result=pd.read_sql_query(sql,conn,params=(plan.limit,))
 evidence={'plan':asdict(plan),'sql':sql,'parameters':[plan.limit],'scope_rows':len(subset),'scope_total':float(subset[col].sum()),'source_sheets':sorted(subset['Source Sheet'].unique()),'row_reference':'Source Row is the original Excel row; header is row 1','scope_months':sorted(int(v) for v in subset.Month.dropna().unique()),'displayed_groups':len(result)}
 return result,evidence

def safe_csv(frame):
 result=frame.copy()
 for col in result.select_dtypes(include=['object','string']).columns:
  result[col]=result[col].map(lambda v: "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@','\t','\r')) else v)
 return result.to_csv(index=False).encode('utf-8-sig')
