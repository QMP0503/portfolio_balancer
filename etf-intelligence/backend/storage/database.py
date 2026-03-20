"""
Database connection and query helpers for the ETF Portfolio Intelligence System.

Owns the async SQLAlchemy engine, session factory, and all raw SQL queries.
No business logic lives here — only connection management and data retrieval.
"""

from collections.abc import AsyncGenerator
from datetime import date

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


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

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
            price,
            volume
        FROM quotes
        ORDER BY ticker, time DESC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        return [row._asdict() for row in result.fetchall()]


async def insert_quotes(quotes: list[dict]) -> int:
    """Insert validated quote dicts into the quotes table.

    Skips rows where price is None. Returns count of inserted rows.

    Args:
        quotes: List of validated dicts from validator.py.

    Returns:
        Number of rows inserted.
    """
    # Filter out any rows missing price — they cannot be stored usefully
    rows = [q for q in quotes if q.get("price") is not None]
    if not rows:
        return 0

    # Named placeholders match the dict keys from validate_quote()
    query = text("""
        INSERT INTO quotes (time, ticker, bid, ask, spread, price, volume)
        VALUES (:time, :ticker, :bid, :ask, :spread, :price, :volume)
    """)

    async with AsyncSessionLocal() as session:
        await session.execute(query, rows)
        await session.commit()

    return len(rows)


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
            price,
            volume
        FROM quotes
        WHERE ticker = :ticker
          AND time >= NOW() - INTERVAL '1 day' * :days
        ORDER BY time ASC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"ticker": ticker, "days": days})
        return [row._asdict() for row in result.fetchall()]


# ---------------------------------------------------------------------------
# Daily summaries
# ---------------------------------------------------------------------------

async def fetch_daily_summary(target_date: date) -> list[dict]:
    """Return daily summary rows for all tickers on a given date.

    Args:
        target_date: The date to query.

    Returns:
        List of dicts with keys: date, ticker, avg_spread, min_spread,
        max_spread, volatility_score. Empty list if no data for that date.
    """
    # Parameterized date avoids injection while supporting date objects
    query = text("""
        SELECT date, ticker, avg_spread, min_spread, max_spread, volatility_score
        FROM daily_summaries
        WHERE date = :target_date
        ORDER BY ticker ASC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"target_date": target_date})
        return [row._asdict() for row in result.fetchall()]


# ---------------------------------------------------------------------------
# Portfolios
# ---------------------------------------------------------------------------

async def fetch_portfolios(user_id: int) -> list[dict]:
    """Return all portfolios belonging to a user.

    Args:
        user_id: Authenticated user's ID.

    Returns:
        List of dicts with keys: id, user_id, account_name, created_at.
    """
    # Filter strictly to the authenticated user — never return other users' portfolios
    query = text("""
        SELECT id, user_id, account_name, created_at
        FROM portfolios
        WHERE user_id = :user_id
        ORDER BY created_at ASC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"user_id": user_id})
        return [row._asdict() for row in result.fetchall()]


async def create_portfolio(user_id: int, account_name: str) -> dict:
    """Create a new portfolio for a user and return the created row.

    Args:
        user_id:      Authenticated user's ID.
        account_name: Free-text account label (e.g. 'TFSA', 'FHSA').

    Returns:
        Dict with keys: id, user_id, account_name, created_at.
    """
    # RETURNING so the caller has the new ID without a second query
    query = text("""
        INSERT INTO portfolios (user_id, account_name)
        VALUES (:user_id, :account_name)
        RETURNING id, user_id, account_name, created_at
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"user_id": user_id, "account_name": account_name})
        await session.commit()
        return result.fetchone()._asdict()


async def fetch_portfolio_allocations(portfolio_id: int) -> list[dict]:
    """Return all ETF allocations for a portfolio.

    Args:
        portfolio_id: The portfolio to query.

    Returns:
        List of dicts with keys: id, portfolio_id, ticker, target_pct, goal.
    """
    # Ordered by ticker for consistent API responses
    query = text("""
        SELECT id, portfolio_id, ticker, target_pct, goal
        FROM portfolio_allocations
        WHERE portfolio_id = :portfolio_id
        ORDER BY ticker ASC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"portfolio_id": portfolio_id})
        return [row._asdict() for row in result.fetchall()]


async def upsert_portfolio_allocation(
    portfolio_id: int, ticker: str, target_pct: float, goal: str | None
) -> None:
    """Insert or update a single ETF allocation for a portfolio.

    Args:
        portfolio_id: The portfolio to update.
        ticker:       ETF ticker symbol, e.g. 'VFV.TO'.
        target_pct:   Target allocation percentage (0–100).
        goal:         Optional goal description for the user.
    """
    # ON CONFLICT on the unique (portfolio_id, ticker) pair
    query = text("""
        INSERT INTO portfolio_allocations (portfolio_id, ticker, target_pct, goal)
        VALUES (:portfolio_id, :ticker, :target_pct, :goal)
        ON CONFLICT (portfolio_id, ticker) DO UPDATE
            SET target_pct = EXCLUDED.target_pct,
                goal       = EXCLUDED.goal
    """)

    async with AsyncSessionLocal() as session:
        await session.execute(query, {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "target_pct": target_pct,
            "goal": goal,
        })
        await session.commit()


# ---------------------------------------------------------------------------
# Holdings
# ---------------------------------------------------------------------------

async def fetch_holdings(portfolio_id: int) -> list[dict]:
    """Return all holdings for a portfolio.

    Args:
        portfolio_id: The portfolio to query.

    Returns:
        List of dicts with keys: portfolio_id, ticker, shares, last_updated.
    """
    # Scoped strictly to one portfolio
    query = text("""
        SELECT portfolio_id, ticker, shares, last_updated
        FROM holdings
        WHERE portfolio_id = :portfolio_id
        ORDER BY ticker ASC
    """)

    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"portfolio_id": portfolio_id})
        return [row._asdict() for row in result.fetchall()]


async def upsert_holding(portfolio_id: int, ticker: str, shares: float) -> None:
    """Insert or update the share count for a ticker in a portfolio.

    Args:
        portfolio_id: The portfolio to update.
        ticker:       ETF ticker symbol, e.g. 'VFV.TO'.
        shares:       New total share count (replaces existing value).
    """
    # ON CONFLICT on composite PK (portfolio_id, ticker)
    query = text("""
        INSERT INTO holdings (portfolio_id, ticker, shares, last_updated)
        VALUES (:portfolio_id, :ticker, :shares, NOW())
        ON CONFLICT (portfolio_id, ticker) DO UPDATE
            SET shares       = EXCLUDED.shares,
                last_updated = NOW()
    """)

    async with AsyncSessionLocal() as session:
        await session.execute(query, {
            "portfolio_id": portfolio_id,
            "ticker": ticker,
            "shares": shares,
        })
        await session.commit()
