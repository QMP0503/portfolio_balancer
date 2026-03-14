"""storage/summarizer.py — Computes and stores daily spread summaries from raw quotes."""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from storage.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# -- Queries ------------------------------------------------------------------

# Aggregate spread stats for a single day, grouped by ticker.
# Uses time_bucket to align rows to day boundaries before grouping.
# Only rows with a non-null spread are included (outside-hours rows are excluded).
_COMPUTE_SUMMARY_SQL = text("""
    INSERT INTO daily_summaries (date, ticker, avg_spread, min_spread, max_spread, volatility_score)
    SELECT
        time_bucket('1 day', time)::date AS date,
        ticker,
        AVG(spread)                      AS avg_spread,
        MIN(spread)                      AS min_spread,
        MAX(spread)                      AS max_spread,
        STDDEV(spread)                   AS volatility_score
    FROM quotes
    WHERE time >= :day_start
      AND time <  :day_end
      AND spread IS NOT NULL
    GROUP BY time_bucket('1 day', time), ticker
    ON CONFLICT (date, ticker) DO UPDATE
        SET avg_spread       = EXCLUDED.avg_spread,
            min_spread       = EXCLUDED.min_spread,
            max_spread       = EXCLUDED.max_spread,
            volatility_score = EXCLUDED.volatility_score
""")


# -----------------------------------------------------------------------------

async def compute_daily_summary(target_date: date) -> None:
    """Aggregate raw quotes for target_date into daily_summaries.

    Idempotent — safe to re-run if quotes are added late.

    Args:
        target_date: The calendar date to summarize.
    """
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    async with AsyncSessionLocal() as session:
        await session.execute(_COMPUTE_SUMMARY_SQL, {"day_start": day_start, "day_end": day_end})
        await session.commit()

    logger.info("Daily summary computed for %s", target_date)


async def backfill_summaries(start_date: date, end_date: date) -> None:
    """Compute daily summaries for every date in [start_date, end_date].

    Args:
        start_date: First date to summarize (inclusive).
        end_date:   Last date to summarize (inclusive).
    """
    current = start_date
    total = (end_date - start_date).days + 1
    completed = 0

    while current <= end_date:
        await compute_daily_summary(current)
        current += timedelta(days=1)
        completed += 1
        logger.info("Backfill progress: %d/%d", completed, total)
