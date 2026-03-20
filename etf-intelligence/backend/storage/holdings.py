"""storage/holdings.py — All database queries for the holdings table."""

from sqlalchemy import text

from storage.database import AsyncSessionLocal


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
