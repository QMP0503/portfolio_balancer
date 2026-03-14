"""
tests/ingestion/test_validator.py

Unit tests for ingestion/validator.py.
Pure function tests — no DB, no async, no mocking.
"""

from datetime import datetime, timezone

import pytest

from ingestion.validator import validate_quote

NOW = datetime.now(timezone.utc)


def _base_quote(**overrides) -> dict:
    """Return a valid quote dict with optional field overrides."""
    base = {
        "ticker": "VFV.TO",
        "time": NOW,
        "bid": 161.50,
        "ask": 161.70,
        "price": 161.60,
        "volume": 1000,
    }
    return {**base, **overrides}


# ---------------------------------------------------------------------------
# Valid cases
# ---------------------------------------------------------------------------

def test_valid_quote_with_bid_ask_computes_spread():
    result = validate_quote(_base_quote())
    assert result is not None
    assert round(result["spread"], 4) == round(161.70 - 161.50, 4)


def test_valid_quote_without_bid_ask_returns_none_spread():
    """Outside market hours bid/ask are None — should still pass."""
    result = validate_quote(_base_quote(bid=None, ask=None))
    assert result is not None
    assert result["spread"] is None


def test_valid_quote_preserves_all_original_fields():
    quote = _base_quote()
    result = validate_quote(quote)
    for key in ("ticker", "time", "bid", "ask", "price", "volume"):
        assert result[key] == quote[key]


# ---------------------------------------------------------------------------
# Price rejections
# ---------------------------------------------------------------------------

def test_rejects_none_price():
    assert validate_quote(_base_quote(price=None)) is None


def test_rejects_zero_price():
    assert validate_quote(_base_quote(price=0)) is None


def test_rejects_negative_price():
    assert validate_quote(_base_quote(price=-1.0)) is None


# ---------------------------------------------------------------------------
# Volume rejections
# ---------------------------------------------------------------------------

def test_rejects_negative_volume():
    assert validate_quote(_base_quote(volume=-1)) is None


def test_allows_zero_volume():
    result = validate_quote(_base_quote(volume=0))
    assert result is not None


def test_allows_none_volume():
    result = validate_quote(_base_quote(volume=None))
    assert result is not None


# ---------------------------------------------------------------------------
# Spread rejections
# ---------------------------------------------------------------------------

def test_rejects_crossed_market():
    assert validate_quote(_base_quote(bid=162.00, ask=161.50)) is None


def test_rejects_zero_bid():
    assert validate_quote(_base_quote(bid=0)) is None


def test_rejects_zero_ask():
    assert validate_quote(_base_quote(ask=0)) is None


def test_rejects_spread_exceeding_2_percent():
    # price=100, spread=3.0 → ratio=0.03 > 0.02
    assert validate_quote(_base_quote(bid=98.50, ask=101.50, price=100.0)) is None


def test_allows_spread_at_2_percent_boundary():
    # price=100, spread=2.0 → ratio=0.02, exactly at limit — should pass
    result = validate_quote(_base_quote(bid=99.00, ask=101.00, price=100.0))
    assert result is not None


def test_spread_ratio_uses_price_not_absolute():
    """A $2 spread on a $200 ETF is 1% — should pass."""
    result = validate_quote(_base_quote(bid=199.00, ask=201.00, price=200.0))
    assert result is not None
