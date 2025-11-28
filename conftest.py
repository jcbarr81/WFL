import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_PATH = BASE_DIR / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
