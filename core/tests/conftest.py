import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import django

# Project root must be on path so "aivora" can be imported
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

load_dotenv()


def pytest_configure():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aivora.settings_test")
    django.setup()
