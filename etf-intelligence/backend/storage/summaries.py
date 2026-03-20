"""storage/summaries.py — All database queries for the daily_summaries table."""

from datetime import date

from sqlalchemy import text

from storage.database import AsyncSessionLocal


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
