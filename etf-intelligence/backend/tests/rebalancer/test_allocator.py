"""Tests for rebalancer/allocator.py.

Pure function tests — no DB, no async.
"""

import pytest

from rebalancer.allocator import (
    BuyRecommendation,
    HoldingSnapshot,
    _compute_needed_cad,
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
# _compute_needed_cad
# ---------------------------------------------------------------------------

def test_needed_cad_excludes_ticker_above_target() -> None:
    """A ticker whose value already exceeds its target in new_total is excluded."""
    # HXQ at $50k, contribution $1k → new_total $51k, HXQ target 40% = $20.4k < $50k
    values = {"HXQ.TO": 50_000.0, "VFV.TO": 0.0, "VCN.TO": 0.0, "ZEM.TO": 0.0}
    new_total = 51_000.0
    needed = _compute_needed_cad(values, new_total, TARGETS)
    assert "HXQ.TO" not in needed


def test_needed_cad_empty_portfolio() -> None:
    """When portfolio is empty, every ticker needs its full target share."""
    values = {t: 0.0 for t in TARGETS}
    new_total = 1000.0
    needed = _compute_needed_cad(values, new_total, TARGETS)
    assert set(needed.keys()) == set(TARGETS.keys())
    assert abs(needed["HXQ.TO"] - 400.0) < 0.01
    assert abs(needed["VFV.TO"] - 350.0) < 0.01
    assert abs(needed["VCN.TO"] - 150.0) < 0.01
    assert abs(needed["ZEM.TO"] - 100.0) < 0.01


def test_needed_cad_balanced_portfolio_with_contribution() -> None:
    """A perfectly balanced portfolio still needs buys for every ticker
    when a contribution is added — each ticker must grow proportionally."""
    # $10k balanced: HXQ=$4k, VFV=$3.5k, VCN=$1.5k, ZEM=$1k → add $1k → new $11k
    values = {"HXQ.TO": 4000.0, "VFV.TO": 3500.0, "VCN.TO": 1500.0, "ZEM.TO": 1000.0}
    new_total = 11_000.0
    needed = _compute_needed_cad(values, new_total, TARGETS)
    assert set(needed.keys()) == set(TARGETS.keys())


def test_needed_cad_overweight_excluded() -> None:
    """Only tickers with a positive shortfall are returned."""
    # VFV at 60% vs 35% target — excluded from needs
    values = {"HXQ.TO": 0.0, "VFV.TO": 6000.0, "VCN.TO": 0.0, "ZEM.TO": 0.0}
    new_total = 11_000.0
    needed = _compute_needed_cad(values, new_total, TARGETS)
    assert "VFV.TO" not in needed
    assert "HXQ.TO" in needed


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


def test_recommendations_all_four_tickers_on_balanced_portfolio() -> None:
    """Adding contribution to a balanced portfolio should recommend all 4 tickers."""
    prices = {"HXQ.TO": 100.0, "VFV.TO": 100.0, "VCN.TO": 100.0, "ZEM.TO": 100.0}
    shares = {"HXQ.TO": 40, "VFV.TO": 35, "VCN.TO": 15, "ZEM.TO": 10}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(1200.0, holdings, TARGETS)
    tickers = {r.ticker for r in recs}
    assert tickers == set(TARGETS.keys())


def test_recommendations_skip_massively_overweight_ticker() -> None:
    """A ticker so overweight its value exceeds its target in new_total gets no buy."""
    # HXQ at $50k (97%) — even after $1200 contrib, target is only 40% of $51.2k = $20.5k < $50k
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


def test_negative_contribution_raises() -> None:
    """Negative contribution must raise ValueError."""
    holdings = [HoldingSnapshot(ticker="VFV.TO", shares=10, price=100.0)]
    with pytest.raises(ValueError):
        compute_buy_recommendations(-100.0, holdings, TARGETS)


def test_recommendations_have_pct_fields() -> None:
    """Every recommendation must include current_pct and target_pct."""
    prices = {"HXQ.TO": 50.0, "VFV.TO": 108.0, "VCN.TO": 68.0, "ZEM.TO": 40.0}
    shares = {t: 0 for t in prices}
    holdings = _make_holdings(prices, shares)
    recs = compute_buy_recommendations(1200.0, holdings, TARGETS)
    for r in recs:
        assert r.current_pct == 0.0
        assert r.target_pct == TARGETS[r.ticker]
