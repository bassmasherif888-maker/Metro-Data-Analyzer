import streamlit as st
import plotly.express as px
from analytics import load_file, execute, parse_question, Plan, METRICS, safe_csv
from security import require_access
from assistant import ai_plan

st.set_page_config(page_title='Metro Intelligence',page_icon='📊',layout='wide')
st.title('Metro | E-commerce Intelligence Hub')
role=require_access(st)
st.caption('Executive decisions grounded in recorded SIAM data • ذكاء أعمال مترو')
st.info('Sales are recorded SIAM sales, not profit or verified net revenue. Orders, AOV and unique customers are unavailable. Observed patterns do not establish causes.')
upload=st.file_uploader('Upload a private SIAM workbook / ارفع ملف المبيعات',type=['xlsx'],max_upload_size=200)
if not upload:
 st.info('Upload a workbook to start. No demonstration numbers are presented as business results.'); st.stop()
try:
 # Session-scoped only: no cross-user data cache or disk persistence.
 import hashlib
 digest=hashlib.sha256(upload.getvalue()).hexdigest()
 if st.session_state.get('digest')!=digest:
  st.session_state['dataset']=load_file(upload.getvalue()); st.session_state['digest']=digest
 ds=st.session_state['dataset']
except Exception as exc:
 st.error(f'Workbook validation failed: {exc}'); st.stop()
for warning in ds.warnings: st.warning(warning)
st.sidebar.header('Decision scope / نطاق التحليل')
channels=st.sidebar.multiselect('Channels',sorted(ds.data.Channel.unique()),default=sorted(ds.data.Channel.unique()))
months=st.sidebar.multiselect('Months',sorted(ds.data.Month.dropna().astype(int).unique()),default=sorted(ds.data.Month.dropna().astype(int).unique()))
branches=st.sidebar.multiselect('Branches',sorted(ds.data['Site Description'].unique()))
scope=ds.data[ds.data.Channel.isin(channels)&ds.data.Month.isin(months)]
if branches: scope=scope[scope['Site Description'].isin(branches)]
st.caption(f'Workbook SHA-256: {ds.fingerprint} • Selected rows: {len(scope):,}. Month filters exclude invalid/missing months. No year or currency is inferred from a filename.')
if scope.empty: st.warning('No rows in the selected scope.'); st.stop()
for cell,(metric,col) in zip(st.columns(3),METRICS.items()):
 value=scope[col].sum() if col in scope and scope[col].notna().all() else None
 cell.metric(col,f'{value:,.2f}' if value is not None else 'Unavailable')
executive,assistant,quality=st.tabs(['لوحة الإدارة / Executive decisions','اسألي مترو / Ask Metro','جودة البيانات والمطابقة / Quality'])
with executive:
 for dim,title in [('channel','Channel contribution'),('month','Monthly movement'),('branch','Leading branches')]:
  try:
   result,evidence=execute(scope,Plan(dimension=dim,limit=12 if dim=='month' else 10))
   st.subheader(title)
   fig=px.line(result,x='grouping',y='value',markers=True) if dim=='month' else px.bar(result,x='grouping',y='value')
   st.plotly_chart(fig,width='stretch')
   if dim=='channel':
    leader=result.iloc[0]
    st.write(f"Largest recorded channel: {leader.grouping}, {leader.value:,.2f}; evidence: {evidence['scope_rows']:,} selected source rows.")
    st.write('Recommended action: review channel mix alongside validated costs and service levels before reallocating budget.')
   if dim=='month' and len(result)>1:
    previous,current=result.iloc[-2],result.iloc[-1]
    if current.grouping-previous.grouping==1 and previous.value!=0:
     change=(current.value/previous.value-1)*100
     st.write(f'Last two available consecutive months: {change:+.1f}% recorded sales movement. Completeness of each month is unverified.')
     st.write('Recommended action: reconcile period coverage and investigate branch/product contributions; do not attribute the change to a campaign without evidence.')
   with st.expander('Evidence'): st.json(evidence)
  except ValueError as exc: st.warning(str(exc))
with assistant:
 st.write('Arabic and English questions produce a proposed query for review. Dashboard filters remain in effect.')
 st.caption('Examples: Top 10 branches by sales in Talabat · أعلى 5 منتجات مبيعات في طلبات · monthly sales · quantity by channel month 3')
 question=st.text_input('Business question / سؤال الأعمال',max_chars=1000)
 try: config=dict(st.secrets.get('ai',{}))
 except Exception: config={}
 use_ai=st.checkbox('Use configured AI to interpret this question (question text is sent to the approved provider; workbook rows are never sent)',disabled=not bool(config))
 if not config: st.caption('AI provider is not configured. The local bilingual guided interpreter is available; it is rule based, not an LLM.')
 if st.button('١. جهّزي السؤال / Prepare validated query'):
  st.session_state.pop('proposal',None)
  try:
   plan=ai_plan(question,config) if use_ai else parse_question(question)
   st.session_state.proposal=(question,plan)
  except Exception:
   st.error('Cannot safely interpret this question. Use recorded sales or quantity with a channel, branch, product, or month grouping; unavailable or causal metrics cannot be answered.')
 proposal=st.session_state.get('proposal')
 if proposal and proposal[0]==question:
  from dataclasses import asdict
  st.json(asdict(proposal[1]))
  st.caption('Review metric, grouping, channel and month filters before executing. Only the first indicated number of groups is displayed.')
  if st.button('٢. اعرضي الإجابة / Run reviewed query'):
   try:
    result,evidence=execute(scope,proposal[1]); st.dataframe(result,hide_index=True)
    st.plotly_chart(px.bar(result,x='grouping',y='value'),width='stretch')
    st.write(f"Total for the full matched scope: {evidence['scope_total']:,.2f}. Displayed groups may be a subset of that total.")
    st.json({'workbook_sha256':ds.fingerprint,**evidence,'dashboard_filters':{'channels':channels,'months':[int(m) for m in months],'branches':branches}})
    st.info('Action: validate coverage and investigate leading or declining groups before changing allocation. This result is descriptive and does not establish causation.')
    if role=='analyst': st.download_button('Export result',safe_csv(result),'metro_query.csv','text/csv')
   except ValueError as exc: st.error(str(exc))
with quality:
 st.dataframe(ds.reconciliation,hide_index=True)
 st.caption('PASS means numeric row totals survived ingestion, not that the finance ledger independently agrees. Duplicates are retained. Invalid numeric values block affected metrics. No missing periods are filled with zeros.')
 st.write('Payment mapping: Talabat cash via rider and card in Talabat remain separate details within one Talabat channel.')
 if role=='analyst':
  st.download_button('Export reconciliation',safe_csv(ds.reconciliation),'metro_reconciliation.csv','text/csv')
