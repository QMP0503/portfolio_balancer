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

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/etf_test",
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
