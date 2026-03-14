"""
ingestion/fetcher.py

Fetches current bid/ask/price/volume for ETFs from yfinance.
Uses asyncio.gather() for concurrent fetching — all 4 tickers in parallel.
No blocking calls inside async functions; yfinance is wrapped in asyncio.to_thread().
"""

import asyncio
import logging
from datetime import datetime, timezone

import yfinance as yf

logger = logging.getLogger(__name__)


async def fetch_one(ticker: str) -> dict:
    """Fetch current market data for a single ETF ticker.

    Uses yfinance fast_info to avoid a full historical download.
    Returns a dict with raw values — validation happens in validator.py.
    Returns None fields if yfinance provides no data (e.g. outside market hours).

    Args:
        ticker: The ETF ticker symbol (e.g. "VFV.TO").

    Returns:
        A dict with keys: ticker, time, bid, ask, price, volume.
    """
    def _blocking_fetch() -> dict:
        info = yf.Ticker(ticker).fast_info
        return {
            "ticker": ticker,
            "time": datetime.now(timezone.utc),
            "bid": _safe_float(getattr(info, "bid", None)),
            "ask": _safe_float(getattr(info, "ask", None)),
            "price": _safe_float(getattr(info, "last_price", None)),
            "volume": _safe_int(getattr(info, "last_volume", None)),
        }

    try:
        result = await asyncio.to_thread(_blocking_fetch)
        logger.debug("Fetched %s: bid=%s ask=%s price=%s", ticker, result["bid"], result["ask"], result["price"])
        return result
    except Exception as exc:
        logger.error("Failed to fetch %s: %s", ticker, exc)
        return {
            "ticker": ticker,
            "time": datetime.now(timezone.utc),
            "bid": None,
            "ask": None,
            "price": None,
            "volume": None,
        }


async def fetch_all(tickers: list[str]) -> list[dict]:
    """Fetch current market data for all tickers concurrently.

    Uses asyncio.gather() with return_exceptions=True so a single
    failed ticker does not abort the entire cycle.

    Args:
        tickers: List of ETF ticker symbols.

    Returns:
        List of quote dicts, one per ticker. Failed tickers return
        an all-None dict (logged inside fetch_one).
    """
    results = await asyncio.gather(
        *[fetch_one(ticker) for ticker in tickers],
        return_exceptions=True,
    )

    quotes: list[dict] = []
    for ticker, result in zip(tickers, results):
        if isinstance(result, BaseException):
            logger.error("Unexpected exception for %s: %s", ticker, result)
            quotes.append({
                "ticker": ticker,
                "time": datetime.now(timezone.utc),
                "bid": None,
                "ask": None,
                "price": None,
                "volume": None,
            })
        else:
            quotes.append(result)

    return quotes


def _safe_float(value: object) -> float | None:
    """Convert a value to float, returning None if conversion fails."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(value: object) -> int | None:
    """Convert a value to int, returning None if conversion fails."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
