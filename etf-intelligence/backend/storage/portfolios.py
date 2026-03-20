"""storage/portfolios.py — All database queries for portfolios and portfolio_allocations."""

from sqlalchemy import text

from storage.database import AsyncSessionLocal


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
