"""tests/api/conftest.py — DB setup, TestClient, and shared auth fixtures.

Applies to all tests under tests/api/ only.
Requires a running TimescaleDB instance on localhost:5433.
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
_HOST = os.getenv("POSTGRES_HOST", "db")
_PORT = os.getenv("POSTGRES_PORT", "5432")
_TEST_DB = "etf_test"
_DSN = f"postgresql://{_USER}:{_PASS}@{_HOST}:{_PORT}/{_TEST_DB}"
_SCHEMA = Path(__file__).parent.parent.parent / "storage" / "schema.sql"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _create_test_db() -> None:
    """Drop and recreate etf_test to ensure schema is always current."""
    conn = await asyncpg.connect(
        f"postgresql://{_USER}:{_PASS}@{_HOST}:{_PORT}/postgres"
    )
    # Terminate any existing connections so DROP DATABASE succeeds
    await conn.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = $1",
        _TEST_DB,
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{_TEST_DB}"')
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
    # Order matters — child tables first to satisfy FK constraints
    for table in ("holdings", "transactions", "portfolio_allocations", "portfolios",
                  "daily_summaries", "quotes", "users"):
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
def clean_tables(setup_test_db: None, client: TestClient):
    """Wipe all rows and clear auth cookies after every test."""
    yield
    asyncio.run(_clean_tables())
    client.cookies.clear()  # Reset auth state so unauthenticated tests start clean


@asynccontextmanager
async def _no_op_lifespan(app):
    """Replace the real lifespan so the scheduler does not start in tests."""
    yield


@pytest.fixture(scope="session")
def client(setup_test_db: None) -> TestClient:
    """Return a TestClient with scheduler disabled."""
    with patch.object(app.router, "lifespan_context", _no_op_lifespan):
        with TestClient(app, cookies={}) as c:
            yield c


@pytest.fixture()
def auth_cookies(client: TestClient) -> dict:
    """Register a test user, log in, and return the auth cookie dict."""
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
    assert response.status_code == 200
    # Extract the cookie value set by the server
    token = response.cookies.get("access_token")
    return {"access_token": token}


@pytest.fixture()
def portfolio_id(client: TestClient, auth_cookies: dict) -> int:
    """Create a test portfolio and return its ID."""
    response = client.post(
        "/portfolios",
        json={"account_name": "TFSA"},
        cookies=auth_cookies,
    )
    assert response.status_code == 201
    return response.json()["id"]
