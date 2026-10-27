"""Public, opt-in entrypoint for non-confidential data. No OIDC needed."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('app.py')),
               init_globals={'PUBLIC_DEMO': True}, run_name='__main__')
