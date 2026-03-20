"""routers/rebalancer.py — Buy recommendation and execution timing endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.settings import TARGET_ALLOCATIONS, TICKERS
from storage.database import fetch_holdings, fetch_latest_quotes
from rebalancer.allocator import BuyRecommendation, HoldingSnapshot, compute_buy_recommendations
from rebalancer.timing import ExecutionWindow, get_execution_windows

router = APIRouter(prefix="/rebalancer", tags=["rebalancer"])


class RebalancerResponse(BaseModel):
    """Buy recommendations for a given contribution amount."""

    contribution_cad: float
    recommendations: list[BuyRecommendation]
    total_cost: float
    leftover_cad: float


@router.get("/recommend", response_model=RebalancerResponse)
async def get_recommendations(contribution_cad: float) -> RebalancerResponse:
    """Return buy recommendations for a given CAD contribution amount.

    Reads current holdings and latest prices from DB, then runs
    the deficit-based allocation algorithm.
    """
    if contribution_cad <= 0:
        raise HTTPException(status_code=422, detail="contribution_cad must be positive")

    holdings_rows = await fetch_holdings()
    quotes_rows = await fetch_latest_quotes()
    prices = {q["ticker"]: q["price"] for q in quotes_rows if q["price"] is not None}
    shares = {h["ticker"]: h["shares"] for h in holdings_rows}

    snapshots = [
        HoldingSnapshot(ticker=t, shares=shares.get(t, 0.0), price=prices[t])
        for t in TICKERS
        if t in prices
    ]

    if not snapshots:
        raise HTTPException(status_code=503, detail="No price data available — market may be closed")

    recs = compute_buy_recommendations(contribution_cad, snapshots, TARGET_ALLOCATIONS)
    total_cost = sum(r.total_cost for r in recs)

    return RebalancerResponse(
        contribution_cad=contribution_cad,
        recommendations=recs,
        total_cost=round(total_cost, 2),
        leftover_cad=round(contribution_cad - total_cost, 2),
    )


@router.get("/timing", response_model=list[ExecutionWindow])
async def get_timing() -> list[ExecutionWindow]:
    """Return the best execution window for each tracked ETF."""
    return get_execution_windows()
