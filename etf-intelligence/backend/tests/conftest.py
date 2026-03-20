"""tests/conftest.py — Set test DATABASE_URL before any module imports it.

This file is loaded by pytest before any test module is collected.
The env var must be set here — at module level, not inside a fixture —
so settings.py picks it up on its first import.

Also forces SelectorEventLoop on Windows — asyncpg is incompatible with
the default ProactorEventLoop used by Python on Windows.
"""

import asyncio
import os
import sys

_user = os.getenv("POSTGRES_USER", "postgres")
_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
_host = os.getenv("POSTGRES_HOST", "db")
_port = os.getenv("POSTGRES_PORT", "5432")

# Force-override — DATABASE_URL may already be set by docker-compose pointing at etf_db.
# Tests must always use etf_test so they never touch production data.
os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{_user}:{_pass}@{_host}:{_port}/etf_test"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
