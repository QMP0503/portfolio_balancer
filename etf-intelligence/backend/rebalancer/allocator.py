"""rebalancer/allocator.py — Core buy recommendation algorithm.

Computes how to allocate a CAD contribution across underweight ETFs.
Pure functions only — no DB access, no side effects.
"""

import math
from pydantic import BaseModel


class HoldingSnapshot(BaseModel):
    """Current state of a single ETF position with its live price."""

    ticker: str
    shares: float
    price: float


class BuyRecommendation(BaseModel):
    """A single ETF buy instruction produced by the allocator."""

    ticker: str
    shares_to_buy: int
    price: float
    total_cost: float
    reason: str


def _compute_portfolio_values(holdings: list[HoldingSnapshot]) -> dict[str, float]:
    """Return CAD market value per ticker.

    Args:
        holdings: Current positions with live prices.

    Returns:
        Mapping of ticker to market value in CAD.
    """
    return {h.ticker: h.shares * h.price for h in holdings}


def _compute_deficits(
    values: dict[str, float],
    total_value: float,
    target_allocations: dict[str, float],
) -> dict[str, float]:
    """Return deficit percentage for each underweight ticker.

    A deficit is target_pct - current_pct, kept only when positive.
    When total_value is zero (first purchase), current_pct is 0 for all tickers
    and deficit equals the full target — the math distributes correctly.

    Args:
        values: Market value per ticker.
        total_value: Sum of all ticker values.
        target_allocations: Target percentage per ticker (0–100 scale).

    Returns:
        Mapping of ticker to deficit percentage for underweight tickers only.
    """
    deficits: dict[str, float] = {}
    for ticker, target_pct in target_allocations.items():
        current_pct = (values.get(ticker, 0.0) / total_value * 100) if total_value > 0 else 0.0
        deficit = target_pct - current_pct
        if deficit > 0:
            deficits[ticker] = deficit
    return deficits


def _build_recommendation(
    ticker: str,
    allocated_cad: float,
    price: float,
    deficit_pct: float,
) -> BuyRecommendation:
    """Convert a dollar allocation into a whole-share buy recommendation.

    Args:
        ticker: ETF ticker symbol.
        allocated_cad: Dollars allocated to this ticker.
        price: Current live price per share.
        deficit_pct: How underweight this ticker is (for the reason string).

    Returns:
        BuyRecommendation with shares_to_buy=0 if allocation can't afford 1 share.
    """
    shares_to_buy = math.floor(allocated_cad / price)

    if shares_to_buy == 0:
        return BuyRecommendation(
            ticker=ticker,
            shares_to_buy=0,
            price=price,
            total_cost=0.0,
            reason=f"underweight by {deficit_pct:.1f}% but price ${price:.2f} exceeds remaining budget",
        )

    return BuyRecommendation(
        ticker=ticker,
        shares_to_buy=shares_to_buy,
        price=price,
        total_cost=round(shares_to_buy * price, 2),
        reason=f"underweight by {deficit_pct:.1f}%",
    )


def compute_buy_recommendations(
    contribution_cad: float,
    holdings: list[HoldingSnapshot],
    target_allocations: dict[str, float],
) -> list[BuyRecommendation]:
    """Allocate a CAD contribution across underweight ETFs.

    Splits the contribution proportionally to each underweight ticker's
    deficit (target_pct - current_pct). Overweight tickers are skipped.
    Guarantees total spend <= contribution_cad.

    Args:
        contribution_cad: Amount available to invest in CAD.
        holdings: Current positions with live prices.
        target_allocations: Target percentage per ticker (must sum to 100).

    Returns:
        List of BuyRecommendation, one per underweight ticker.
        Tickers where allocated amount can't buy 1 share have shares_to_buy=0.

    Raises:
        ValueError: If contribution_cad is not positive.
    """
    if contribution_cad <= 0:
        raise ValueError(f"contribution_cad must be positive, got {contribution_cad}")

    values = _compute_portfolio_values(holdings)
    total_value = sum(values.values())
    deficits = _compute_deficits(values, total_value, target_allocations)

    if not deficits:
        return []

    prices = {h.ticker: h.price for h in holdings}
    total_deficit = sum(deficits.values())
    recommendations: list[BuyRecommendation] = []

    for ticker, deficit_pct in deficits.items():
        price = prices.get(ticker, 0.0)
        if price <= 0:
            continue
        allocated = (deficit_pct / total_deficit) * contribution_cad
        recommendations.append(_build_recommendation(ticker, allocated, price, deficit_pct))

    total_cost = sum(r.total_cost for r in recommendations)
    assert total_cost <= contribution_cad, (
        f"Allocator overspent: {total_cost:.2f} > {contribution_cad:.2f}"
    )

    return recommendations
