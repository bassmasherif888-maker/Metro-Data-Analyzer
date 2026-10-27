"""OIDC identity and explicit role assignment; explicit public demo or authenticated private access."""
def role_for(email, verified, roles):
 if verified is not True or not isinstance(email,str): return None
 role=roles.get(email.casefold())
 return role if role in ('executive','analyst') else None

def local_access_allowed(enabled, deployment, address, remote_ip):
 return (enabled == '1' and deployment != 'team'
         and address == '127.0.0.1' and remote_ip in ('127.0.0.1', '::1'))

def require_access(st, public=False):
 import os
 if public:
  if os.environ.get('METRO_DEPLOYMENT') == 'team':
   st.error('Public demo entrypoint is disabled in team deployments.'); st.stop()
  st.warning('نسخة عامة بدون تسجيل دخول — استخدمي بيانات تجريبية أو غير سرية فقط. الملفات تخص جلستك ولا تُعرض تلقائيًا لباقي الزوار.')
  return 'public'

 if os.environ.get('METRO_LOCAL_MODE') == '1':
  if not local_access_allowed('1', os.environ.get('METRO_DEPLOYMENT', ''),
                              st.get_option('server.address'), st.context.ip_address):
   st.error('Local access requires a loopback-only server and a browser on this computer.'); st.stop()
  st.sidebar.info('نسخة شخصية على جهازك فقط — لا تحتاج تسجيل دخول')
  return 'analyst'

 try:
  roles=dict(st.secrets.get('roles',{}))
 except Exception:
  st.error('Access is locked. Configure OIDC and explicit user roles in server secrets.'); st.stop()
 if not st.user.is_logged_in:
  st.info('Sign in with your approved company identity to access Metro data.')
  if st.button('Sign in'): st.login()
  st.stop()
 role=role_for(st.user.get('email'),st.user.get('email_verified'),roles)
 if not role:
  st.error('Your verified identity has no assigned Metro role.')
  if st.button('Sign out'): st.logout()
  st.stop()
 st.sidebar.caption(f'Role: {role}')
 if st.sidebar.button('Sign out'):
  st.session_state.clear(); st.logout(); st.stop()
 return role
