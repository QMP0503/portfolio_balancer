"""tests/api/conftest.py — DB setup, TestClient, and shared auth fixtures.

Applies to all tests under tests/api/ only.
Requires a running TimescaleDB instance on localhost:5432.
Uses a dedicated `etf_test` database — never touches `etf_db`.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import patch

import asyncpg
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load .env from the etf-intelligence root before reading any env vars
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from main import app  # noqa: E402 — must follow load_dotenv

# ---------------------------------------------------------------------------
# Connection config — reads from .env, uses etf_test DB
# ---------------------------------------------------------------------------
_USER = os.getenv("POSTGRES_USER", "postgres")
_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
_HOST = os.getenv("POSTGRES_HOST", "localhost")
_PORT = os.getenv("POSTGRES_PORT", "5433")
_TEST_DB = "etf_test"
_DSN = f"postgresql://{_USER}:{_PASS}@{_HOST}:{_PORT}/{_TEST_DB}"
_SCHEMA = Path(__file__).parent.parent.parent / "storage" / "schema.sql"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _create_test_db() -> None:
    """Create etf_test database if it does not exist."""
    conn = await asyncpg.connect(
        f"postgresql://{_USER}:{_PASS}@{_HOST}:{_PORT}/postgres"
    )
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB
    )
    if not exists:
        await conn.execute(f'CREATE DATABASE "{_TEST_DB}"')
    await conn.close()


async def _apply_schema() -> None:
    """Apply schema.sql to etf_test, ignoring already-exists errors."""
    conn = await asyncpg.connect(_DSN)
    await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    for stmt in _SCHEMA.read_text().split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                await conn.execute(stmt)
            except Exception:
                pass  # table / hypertable / policy already exists
    await conn.close()


async def _clean_tables() -> None:
    """Delete all rows from mutable tables between tests."""
    conn = await asyncpg.connect(_DSN)
    for table in ("holdings", "transactions", "daily_summaries", "quotes", "users"):
        await conn.execute(f"DELETE FROM {table}")  # noqa: S608 — test-only, no user input
    await conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> None:
    """Create etf_test DB and apply schema once per session."""
    asyncio.run(_create_test_db())
    asyncio.run(_apply_schema())


@pytest.fixture(autouse=True)
def clean_tables(setup_test_db: None):
    """Wipe all rows after every test so each test starts clean."""
    yield
    asyncio.run(_clean_tables())


@asynccontextmanager
async def _no_op_lifespan(app):
    """Replace the real lifespan so the scheduler does not start in tests."""
    yield


@pytest.fixture(scope="session")
def client(setup_test_db: None) -> TestClient:
    """Return a TestClient with scheduler disabled."""
    with patch.object(app.router, "lifespan_context", _no_op_lifespan):
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def auth_headers(client: TestClient) -> dict:
    """Register a test user and return Authorization headers."""
    client.post("/auth/register", json={
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPass123!",
    })
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
