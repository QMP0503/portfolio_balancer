"""
Database connection and query helpers for the ETF Portfolio Intelligence System.

Owns the async SQLAlchemy engine, session factory, and all raw SQL queries.
No business logic lives here — only connection management and data retrieval.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import DATABASE_URL

# Ensure the URL uses the asyncpg driver — docker-compose injects a plain postgresql:// URL
_async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_async_url, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for use with FastAPI Depends."""
    async with AsyncSessionLocal() as session:
        yield session


async def fetch_latest_quotes() -> list[dict]:
    """Return the most recent quote row for each ticker.

    Uses a DISTINCT ON query ordered by time descending so each ticker
    appears exactly once with its latest data.
    """
    # DISTINCT ON (ticker) keeps the first row per ticker after ORDER BY
    query = text("""
        SELECT DISTINCT ON (ticker)
            time,
            ticker,
            bid,
            ask,
            spread,
            volume
        FROM quotes
        ORDER BY ticker, time DESC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        return [row._asdict() for row in result.fetchall()]


async def fetch_quote_history(ticker: str, days: int) -> list[dict]:
    """Return minute-level quotes for a ticker over the past N days.

    Args:
        ticker: ETF ticker symbol, e.g. 'VFV.TO'.
        days:   Number of calendar days of history to return.

    Returns:
        List of dicts with keys: time, ticker, bid, ask, spread, volume.
    """
    # NOW() - interval is evaluated server-side; parameterized to prevent injection
    query = text("""
        SELECT
            time,
            ticker,
            bid,
            ask,
            spread,
            volume
        FROM quotes
        WHERE ticker = :ticker
          AND time >= NOW() - INTERVAL '1 day' * :days
        ORDER BY time ASC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"ticker": ticker, "days": days})
        return [row._asdict() for row in result.fetchall()]
