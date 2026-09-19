from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
DATA = Path(os.environ.get('WAYPOINT_DATA', ROOT / 'data' / 'workspace')).resolve()
DATA.mkdir(parents=True, exist_ok=True)
for folder in ('raw', 'processed', 'models', 'results', 'uploads', 'recordings'):
    (DATA / folder).mkdir(exist_ok=True)
DB_URL = 'sqlite:///' + (DATA / 'waypoint.db').as_posix()
MAX_UPLOAD = 128 * 1024 * 1024
VERSION = '1.0.0'
PUBLIC = os.environ.get('WAYPOINT_PUBLIC') == '1'
ADMIN_PASSWORD = os.environ.get('WAYPOINT_ADMIN_PASSWORD', '')
ALLOWED_ORIGINS = frozenset(origin.strip().rstrip('/') for origin in os.environ.get(
    'WAYPOINT_ALLOWED_ORIGINS',
    'http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000,https://localhost:8443,https://127.0.0.1:8443'
).split(',') if origin.strip())
if PUBLIC and len(ADMIN_PASSWORD) < 24:
    raise RuntimeError('Public mode requires WAYPOINT_ADMIN_PASSWORD of at least 24 characters')
if PUBLIC and not os.environ.get('WAYPOINT_ALLOWED_ORIGINS'):
    raise RuntimeError('Public mode requires explicit WAYPOINT_ALLOWED_ORIGINS')
