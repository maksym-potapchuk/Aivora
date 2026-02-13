"""Test settings: import project settings and override only DB and SECRET_KEY."""
import os

# Allow importing aivora.settings without real DB credentials
for key in ("DB_NAME", "DB_USER", "DB_PASSWORD"):
    os.environ.setdefault(key, "test")

from aivora.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
SECRET_KEY = os.getenv("TEST_SECRET_KEY", "test-secret-key-for-pytest")
