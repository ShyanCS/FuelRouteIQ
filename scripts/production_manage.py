"""Local production checks with ignored secret file; never print its values."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.production", override=True)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuelroute.settings")
if os.getenv("DATABASE_URL_UNPOOLED"):
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL_UNPOOLED"]

from django.core.management import execute_from_command_line  # noqa: E402

execute_from_command_line(sys.argv)
