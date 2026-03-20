"""routers/rebalancer.py — Buy recommendation and execution timing endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config.settings import TICKERS
from routers.portfolios import _assert_owns_portfolio
from storage.holdings import fetch_holdings
from storage.portfolios import fetch_portfolio_allocations
from storage.quotes import fetch_latest_quotes
from rebalancer.allocator import BuyRecommendation, HoldingSnapshot, compute_buy_recommendations
from rebalancer.timing import ExecutionWindow, get_execution_windows

router = APIRouter(prefix="/rebalancer", tags=["rebalancer"])


class RebalancerResponse(BaseModel):
    """Buy recommendations for a given contribution amount."""

    contribution_cad: float
    recommendations: list[BuyRecommendation]
    total_cost: float
    leftover_cad: float


@router.get("/{portfolio_id}/recommend", response_model=RebalancerResponse)
async def get_recommendations(
    portfolio_id: int,
    contribution_cad: float,
    user: dict = Depends(get_current_user),
) -> RebalancerResponse:
    """Return buy recommendations for a given CAD contribution amount.

    Reads current holdings, target allocations, and latest prices from DB,
    then runs the deficit-based allocation algorithm.
    """
    if contribution_cad <= 0:
        raise HTTPException(status_code=422, detail="contribution_cad must be positive")

    await _assert_owns_portfolio(portfolio_id, user["user_id"])

    allocation_rows = await fetch_portfolio_allocations(portfolio_id)
    if not allocation_rows:
        raise HTTPException(status_code=422, detail="No allocations set for this portfolio")

    target_allocations = {r["ticker"]: float(r["target_pct"]) for r in allocation_rows}

    holdings_rows = await fetch_holdings(portfolio_id)
    quotes_rows = await fetch_latest_quotes()
    prices = {q["ticker"]: q["price"] for q in quotes_rows if q["price"] is not None}
    shares = {h["ticker"]: h["shares"] for h in holdings_rows}

    # Only include tickers that have both a target allocation and a live price
    snapshots = [
        HoldingSnapshot(ticker=t, shares=float(shares.get(t, 0.0)), price=float(prices[t]))
        for t in TICKERS
        if t in prices and t in target_allocations
    ]

    if not snapshots:
        raise HTTPException(status_code=503, detail="No price data available — market may be closed")

    recs = compute_buy_recommendations(contribution_cad, snapshots, target_allocations)
    total_cost = sum(r.total_cost for r in recs)

    return RebalancerResponse(
        contribution_cad=contribution_cad,
        recommendations=recs,
        total_cost=round(total_cost, 2),
        leftover_cad=round(contribution_cad - total_cost, 2),
    )


@router.get("/timing", response_model=list[ExecutionWindow])
async def get_timing(_: dict = Depends(get_current_user)) -> list[ExecutionWindow]:
    """Return the best execution window for each tracked ETF."""
    return get_execution_windows()
