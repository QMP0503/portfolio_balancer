"""ingestion/validator.py — Validates raw quote dicts before DB insertion."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

MAX_SPREAD_RATIO = 0.02  # reject if (ask - bid) / price > 2%


def validate_quote(quote: dict) -> Optional[dict]:
    """Return quote with spread added, or None if validation fails."""
    ticker = quote.get("ticker", "UNKNOWN")

    if not _price_valid(quote.get("price"), ticker):
        return None

    if not _volume_valid(quote.get("volume"), ticker):
        return None

    bid = quote.get("bid")
    ask = quote.get("ask")
    price = quote["price"]

    spread = _compute_spread(bid, ask, price, ticker)
    if spread is False:
        return None

    return {**quote, "spread": spread}


def _price_valid(price: Optional[float], ticker: str) -> bool:
    """Return True if price is a positive number."""
    if price is None or price <= 0:
        logger.warning("Rejected %s: price missing or zero (price=%s)", ticker, price)
        return False
    return True


def _volume_valid(volume: Optional[int], ticker: str) -> bool:
    """Return True if volume is absent or non-negative."""
    if volume is not None and volume < 0:
        logger.warning("Rejected %s: negative volume (%s)", ticker, volume)
        return False
    return True


def _compute_spread(
    bid: Optional[float],
    ask: Optional[float],
    price: float,
    ticker: str,
) -> Optional[float]:
    """Return spread, None if bid/ask absent, or False if invalid."""
    if bid is None or ask is None:
        return None

    if bid <= 0 or ask <= 0:
        logger.warning("Rejected %s: bid or ask is zero/negative (bid=%s ask=%s)", ticker, bid, ask)
        return False

    if ask < bid:
        logger.warning("Rejected %s: crossed market (bid=%s ask=%s)", ticker, bid, ask)
        return False

    spread = ask - bid
    spread_ratio = spread / price

    if spread_ratio > MAX_SPREAD_RATIO:
        logger.warning(
            "Rejected %s: spread ratio %.4f exceeds %.2f (bid=%s ask=%s price=%s)",
            ticker, spread_ratio, MAX_SPREAD_RATIO, bid, ask, price,
        )
        return False

    return spread
