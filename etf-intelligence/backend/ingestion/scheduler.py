"""ingestion/scheduler.py — APScheduler that runs ingestion during market hours only."""

import logging
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import (
    FETCH_INTERVAL_SECONDS,
    MARKET_CLOSE,
    MARKET_OPEN,
    TICKERS,
    TIMEZONE,
)
from ingestion.fetcher import fetch_all
from ingestion.validator import validate_quote
from storage.quotes import insert_quotes
from storage.summarizer import compute_daily_summary

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone=TIMEZONE)
_open_hour, _open_minute = (int(x) for x in MARKET_OPEN.split(":"))
_close_hour, _close_minute = (int(x) for x in MARKET_CLOSE.split(":"))


async def fetch_and_store() -> None:
    """Fetch quotes for all tickers, validate, and insert into DB."""
    raw = await fetch_all(TICKERS)
    valid = [q for quote in raw if (q := validate_quote(quote)) is not None]
    inserted = await insert_quotes(valid)
    logger.info("Cycle complete: fetched=%d valid=%d inserted=%d", len(raw), len(valid), inserted)


def _start_ingestion() -> None:
    """Add the 60-second ingestion job to the running scheduler."""
    if not _scheduler.get_job("ingestion"):
        _scheduler.add_job(
            fetch_and_store,
            trigger="interval",
            seconds=FETCH_INTERVAL_SECONDS,
            id="ingestion",
        )
        logger.info("Market open — ingestion started")


def _stop_ingestion() -> None:
    """Remove the ingestion job from the scheduler."""
    if _scheduler.get_job("ingestion"):
        _scheduler.remove_job("ingestion")
        logger.info("Market closed — ingestion stopped")


def _within_market_hours() -> bool:
    """Return True if current Toronto time is within market hours."""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    market_open = now.replace(hour=_open_hour, minute=_open_minute, second=0, microsecond=0)
    market_close = now.replace(hour=_close_hour, minute=_close_minute, second=0, microsecond=0)
    return market_open <= now < market_close


async def _run_daily_summary() -> None:
    """Trigger end-of-day summary computation for today."""
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()
    await compute_daily_summary(today)


def start_scheduler() -> None:
    """Start the APScheduler with market-open and market-close cron jobs.

    If currently within market hours, ingestion starts immediately.
    """
    _scheduler.add_job(
        _start_ingestion,
        trigger="cron",
        hour=_open_hour,
        minute=_open_minute,
        id="market_open",
    )
    _scheduler.add_job(
        _stop_ingestion,
        trigger="cron",
        hour=_close_hour,
        minute=_close_minute,
        id="market_close",
    )
    _scheduler.add_job(
        _run_daily_summary,
        trigger="cron",
        hour=_close_hour,
        minute=_close_minute + 1,
        id="daily_summary",
    )

    _scheduler.start()
    logger.info("Scheduler started")

    if _within_market_hours():
        logger.info("Started during market hours — beginning ingestion immediately")
        _start_ingestion()


def stop_scheduler() -> None:
    """Shut down the scheduler cleanly."""
    _scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
