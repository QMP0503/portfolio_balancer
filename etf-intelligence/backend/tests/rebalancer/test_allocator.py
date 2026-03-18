"""Tests for rebalancer/allocator.py.

Pure function tests — no DB, no async.
"""

import pytest

from rebalancer.allocator import (
    BuyRecommendation,
    HoldingSnapshot,
    _compute_deficits,
    _compute_portfolio_values,
    compute_buy_recommendations,
)

TARGETS = {
    "HXQ.TO": 40.0,
    "VFV.TO": 35.0,
    "VCN.TO": 15.0,
    "ZEM.TO": 10.0,
}


# ---------------------------------------------------------------------------
# _compute_portfolio_values
# ---------------------------------------------------------------------------

def test_portfolio_values_basic() -> None:
    """Market value is shares * price per ticker."""
    holdings = [
        HoldingSnapshot(ticker="VFV.TO", shares=10, price=100.0),
        HoldingSnapshot(ticker="ZEM.TO", shares=5, price=40.0),
    ]
    values = _compute_portfolio_values(holdings)
    assert values == {"VFV.TO": 1000.0, "ZEM.TO": 200.0}


def test_portfolio_values_zero_shares() -> None:
    """Zero shares produces zero value, not an error."""
    holdings = [HoldingSnapshot(ticker="VFV.TO", shares=0, price=100.0)]
    assert _compute_portfolio_values(holdings) == {"VFV.TO": 0.0}


# ---------------------------------------------------------------------------
# _compute_deficits
# ---------------------------------------------------------------------------

def test_deficits_excludes_overweight() -> None:
    """Overweight tickers must not appear in deficits."""
    # HXQ at 60% is overweight vs 40% target
    values = {"HXQ.TO": 6000.0, "VFV.TO": 2000.0, "VCN.TO": 1000.0, "ZEM.TO": 1000.0}
    total = sum(values.values())
    deficits = _compute_deficits(values, total, TARGETS)
    assert "HXQ.TO" not in deficits


def test_deficits_zero_total_value() -> None:
    """When portfolio is empty, deficit equals full target for every ticker."""
    values = {t: 0.0 for t in TARGETS}
    deficits = _compute_deficits(values, 0.0, TARGETS)
    assert deficits == TARGETS


def test_deficits_partial_underweight() -> None:
    """Only genuinely underweight tickers appear."""
    # VFV.TO at 50% (target 35%) is overweight; others at 0%
    values = {"HXQ.TO": 0.0, "VFV.TO": 5000.0, "VCN.TO": 0.0, "ZEM.TO": 0.0}
    total = 5000.0
    deficits = _compute_deficits(values, total, TARGETS)
    assert "VFV.TO" not in deficits
    assert set(deficits.keys()) == {"HXQ.TO", "VCN.TO", "ZEM.TO"}


# ---------------------------------------------------------------------------
# compute_buy_recommendations
# ---------------------------------------------------------------------------

def _make_holdings(prices: dict[str, float], shares: dict[str, float]) -> list[HoldingSnapshot]:
    return [HoldingSnapshot(ticker=t, shares=shares.get(t, 0), price=p) for t, p in prices.items()]


def test_recommendations_do_not_overspend() -> None:
    """Total cost of recommendations must never exceed contribution."""
    prices = {"HXQ.TO": 50.0, "VFV.TO": 108.0, "VCN.TO": 68.0, "ZEM.TO": 40.0}
    shares = {"HXQ.TO": 0, "VFV.TO": 0, "VCN.TO": 0, "ZEM.TO": 0}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(1200.0, holdings, TARGETS)
    total_spent = sum(r.total_cost for r in recs)
    assert total_spent <= 1200.0


def test_recommendations_skip_overweight() -> None:
    """An overweight ticker produces no recommendation."""
    # HXQ at 80% — massively overweight vs 40% target
    prices = {"HXQ.TO": 50.0, "VFV.TO": 108.0, "VCN.TO": 68.0, "ZEM.TO": 40.0}
    shares = {"HXQ.TO": 1000, "VFV.TO": 0, "VCN.TO": 0, "ZEM.TO": 0}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(1200.0, holdings, TARGETS)
    tickers = [r.ticker for r in recs]
    assert "HXQ.TO" not in tickers


def test_unaffordable_ticker_included_with_zero_shares() -> None:
    """A ticker whose price exceeds its allocation gets shares_to_buy=0."""
    # ZEM.TO gets ~10% of $50 = $5, but price is $100 — can't afford 1 share
    prices = {"HXQ.TO": 10.0, "VFV.TO": 10.0, "VCN.TO": 10.0, "ZEM.TO": 100.0}
    shares = {t: 0 for t in prices}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(50.0, holdings, TARGETS)
    zem = next((r for r in recs if r.ticker == "ZEM.TO"), None)
    assert zem is not None
    assert zem.shares_to_buy == 0
    assert zem.total_cost == 0.0


def test_empty_recommendations_when_all_overweight() -> None:
    """Returns empty list when every ticker is at or above target."""
    prices = {"HXQ.TO": 100.0, "VFV.TO": 100.0, "VCN.TO": 100.0, "ZEM.TO": 100.0}
    # Exact target weights — nothing is underweight
    shares = {"HXQ.TO": 40, "VFV.TO": 35, "VCN.TO": 15, "ZEM.TO": 10}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(1200.0, holdings, TARGETS)
    assert recs == []


def test_negative_contribution_raises() -> None:
    """Negative contribution must raise ValueError."""
    holdings = [HoldingSnapshot(ticker="VFV.TO", shares=10, price=100.0)]
    with pytest.raises(ValueError):
        compute_buy_recommendations(-100.0, holdings, TARGETS)


def test_reason_string_contains_deficit() -> None:
    """Reason string must mention the underweight percentage."""
    prices = {"HXQ.TO": 50.0, "VFV.TO": 108.0, "VCN.TO": 68.0, "ZEM.TO": 40.0}
    shares = {t: 0 for t in prices}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(1200.0, holdings, TARGETS)
    for r in recs:
        assert "underweight" in r.reason
