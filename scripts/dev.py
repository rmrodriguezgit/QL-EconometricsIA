"""Start the local React workbench and Python bridge, bound to loopback only."""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
python = root / ('.venv/Scripts/python.exe' if sys.platform == 'win32' else '.venv/bin/python')
npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
if not python.exists() or not npm or not (root / 'apps/desktop/node_modules').exists():
    raise SystemExit('Preparación necesaria: uv sync --frozen; npm ci --prefix apps/desktop')
print('Quantlabs: http://127.0.0.1:1420 · Ctrl+C para detener', flush=True)
try:
    raise SystemExit(subprocess.call([npm, 'run', 'dev', '--prefix', 'apps/desktop'], cwd=root))
except KeyboardInterrupt:
    raise SystemExit(130)
