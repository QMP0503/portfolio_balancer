"""rebalancer/allocator.py — Core buy recommendation algorithm.

Computes how to allocate a CAD contribution across ETFs so the portfolio
reaches target weights after the new money is deployed. Pure functions only
— no DB access, no side effects.
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
    current_pct: float
    target_pct: float


def _compute_portfolio_values(holdings: list[HoldingSnapshot]) -> dict[str, float]:
    """Return CAD market value per ticker.

    Args:
        holdings: Current positions with live prices.

    Returns:
        Mapping of ticker to market value in CAD.
    """
    return {h.ticker: h.shares * h.price for h in holdings}


def _compute_needed_cad(
    values: dict[str, float],
    new_total: float,
    target_allocations: dict[str, float],
) -> dict[str, float]:
    """Return dollars each ticker still needs to reach its target in new_total.

    Uses new_total = current portfolio value + incoming contribution as the
    denominator so that even currently-overweight tickers get a buy if their
    dollar value is below their share of the larger post-contribution portfolio.

    Args:
        values: Current market value per ticker.
        new_total: Current portfolio value plus the incoming contribution.
        target_allocations: Target percentage per ticker (0–100 scale).

    Returns:
        Mapping of ticker to CAD needed. Only tickers with a positive shortfall
        are included; tickers already at or above target are excluded.
    """
    needed: dict[str, float] = {}
    for ticker, target_pct in target_allocations.items():
        target_value = new_total * target_pct / 100
        shortfall = target_value - values.get(ticker, 0.0)
        if shortfall > 0:
            needed[ticker] = shortfall
    return needed


def _greedy_fill(
    buy_counts: dict[str, int],
    values: dict[str, float],
    prices: dict[str, float],
    target_allocations: dict[str, float],
    remaining: float,
) -> dict[str, int]:
    """Buy 1 share at a time of the most underweight affordable ticker.

    Runs until no underweight ticker can be purchased with the remaining budget.
    Only considers tickers with a positive deficit — never buys overweight tickers
    just to spend money.

    Args:
        buy_counts: Current whole-share counts per ticker (mutated in place).
        values: Pre-buy market value per ticker.
        prices: Live price per ticker.
        target_allocations: Target percentage per ticker (0–100 scale).
        remaining: Unspent CAD after initial allocation.

    Returns:
        Updated buy_counts.
    """
    while True:
        total = (
            sum(values.get(t, 0) for t in target_allocations)
            + sum(buy_counts.get(t, 0) * prices.get(t, 0) for t in target_allocations)
        )
        best_ticker: str | None = None
        best_deficit = 0.0
        for ticker, target_pct in target_allocations.items():
            price = prices.get(ticker, 0.0)
            if price <= 0 or price > remaining:
                continue
            current_val = values.get(ticker, 0.0) + buy_counts.get(ticker, 0) * price
            current_pct = (current_val / total * 100) if total > 0 else 0.0
            deficit = target_pct - current_pct
            if deficit > best_deficit:
                best_deficit = deficit
                best_ticker = ticker
        if best_ticker is None:
            break
        buy_counts[best_ticker] = buy_counts.get(best_ticker, 0) + 1
        remaining -= prices[best_ticker]
    return buy_counts


def compute_buy_recommendations(
    contribution_cad: float,
    holdings: list[HoldingSnapshot],
    target_allocations: dict[str, float],
) -> list[BuyRecommendation]:
    """Allocate a CAD contribution across ETFs to approach target weights.

    Phase 1: proportional whole-share allocation based on each ticker's shortfall.
    Phase 2: greedy 1-share-at-a-time fill of leftover cash, always buying the
    most underweight affordable ticker, until budget is exhausted.

    Args:
        contribution_cad: Amount available to invest in CAD.
        holdings: Current positions with live prices.
        target_allocations: Target percentage per ticker (must sum to 100).

    Returns:
        List of BuyRecommendation, one per ticker that needs buying.

    Raises:
        ValueError: If contribution_cad is not positive.
    """
    if contribution_cad <= 0:
        raise ValueError(f"contribution_cad must be positive, got {contribution_cad}")

    values = _compute_portfolio_values(holdings)
    total_value = sum(values.values())
    new_total = total_value + contribution_cad
    needed = _compute_needed_cad(values, new_total, target_allocations)
    if not needed:
        return []

    prices = {h.ticker: h.price for h in holdings}
    total_needed = sum(needed.values())
    scale = min(1.0, contribution_cad / total_needed)

    # Phase 1: initial floored allocation
    buy_counts: dict[str, int] = {}
    for ticker, need_cad in needed.items():
        price = prices.get(ticker, 0.0)
        if price > 0:
            buy_counts[ticker] = math.floor(need_cad * scale / price)

    # Phase 2: greedy fill of leftover
    spent = sum(buy_counts.get(t, 0) * prices.get(t, 0) for t in buy_counts)
    buy_counts = _greedy_fill(buy_counts, values, prices, target_allocations, contribution_cad - spent)

    # Build final recommendations for all tickers that were in needed
    recommendations: list[BuyRecommendation] = []
    for ticker in needed:
        price = prices.get(ticker, 0.0)
        if price <= 0:
            continue
        shares = buy_counts.get(ticker, 0)
        current_pct = (values.get(ticker, 0.0) / total_value * 100) if total_value > 0 else 0.0
        recommendations.append(BuyRecommendation(
            ticker=ticker,
            shares_to_buy=shares,
            price=price,
            total_cost=round(shares * price, 2),
            current_pct=round(current_pct, 1),
            target_pct=round(target_allocations[ticker], 1),
        ))

    total_cost = sum(r.total_cost for r in recommendations)
    assert total_cost <= contribution_cad + 0.01, (
        f"Allocator overspent: {total_cost:.2f} > {contribution_cad:.2f}"
    )
    return recommendations
