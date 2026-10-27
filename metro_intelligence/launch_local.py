"""Double-click wrappers use this launcher. Never opens a shared network listener."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
 os.chdir(ROOT)
 if sys.version_info[:2] != (3, 12):
  print('Please install Python 3.12 from python.org, then open Start Metro again.')
  return 1
 python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
 if not python.exists():
  subprocess.run([sys.executable, '-m', 'venv', str(ROOT / '.venv')],check=True)
 marker=ROOT / '.venv' / 'metro-requirements.txt'
 required=(ROOT / 'requirements.lock.txt').read_text()
 if not marker.exists() or marker.read_text()!=required:
  print('First start: installing Metro components. Please wait; internet is required.')
  subprocess.run([str(python),'-m','pip','install','-r',str(ROOT / 'requirements.lock.txt')],check=True)
  marker.write_text(required)
 runtime=os.environ.copy()
 runtime['METRO_LOCAL_MODE']='1'
 runtime['METRO_DEPLOYMENT']='personal'
 print('Metro will open in your browser. Keep this window open. Press Ctrl+C to stop.')
 return subprocess.call([str(python),'-m','streamlit','run','app.py',
  '--server.address=127.0.0.1','--server.port=8501','--server.headless=false',
  '--server.enableXsrfProtection=true','--server.enableCORS=true',
  '--browser.gatherUsageStats=false'],env=runtime)

if __name__=='__main__':
 try: sys.exit(main())
 except (subprocess.CalledProcessError, OSError) as exc:
  print('Metro could not start. Check Python 3.12 and your internet connection.'); sys.exit(1)
