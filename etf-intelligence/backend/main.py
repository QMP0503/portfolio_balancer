"""
FastAPI application entry point for the ETF Portfolio Intelligence System.

This file is a thin router only — no business logic lives here.
All computation lives in ingestion/, storage/, and rebalancer/ modules.
"""

import logging
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import TICKERS, TARGET_ALLOCATIONS
from ingestion.scheduler import start_scheduler, stop_scheduler
from storage.database import (
    fetch_daily_summary,
    fetch_holdings,
    fetch_latest_quotes,
    upsert_holding,
)
from rebalancer.allocator import BuyRecommendation, HoldingSnapshot, compute_buy_recommendations
from rebalancer.timing import ExecutionWindow, get_execution_windows

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""

    status: str
    version: str


class QuoteResponse(BaseModel):
    """Latest market quote for a single ETF."""

    ticker: str
    bid: float | None
    ask: float | None
    spread: float | None
    price: float | None
    volume: int | None


class HoldingResponse(BaseModel):
    """Current share count for a single ETF."""

    ticker: str
    shares: float


class HoldingUpdateRequest(BaseModel):
    """Request body for updating a holding."""

    shares: float


class RebalancerResponse(BaseModel):
    """Buy recommendations for a given contribution amount."""

    contribution_cad: float
    recommendations: list[BuyRecommendation]
    total_cost: float
    leftover_cad: float


class SummaryResponse(BaseModel):
    """Daily spread summary for a single ETF."""

    date: date
    ticker: str
    avg_spread: float | None
    min_spread: float | None
    max_spread: float | None
    volatility_score: float | None


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("ETF Intelligence System starting")
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="ETF Portfolio Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/quotes/latest", response_model=list[QuoteResponse])
async def get_latest_quotes() -> list[QuoteResponse]:
    """Return the most recent stored quote for each tracked ETF."""
    rows = await fetch_latest_quotes()
    return [QuoteResponse(**row) for row in rows]


@app.get("/holdings", response_model=list[HoldingResponse])
async def get_holdings() -> list[HoldingResponse]:
    """Return current share counts for all tracked ETFs."""
    rows = await fetch_holdings()
    return [HoldingResponse(**row) for row in rows]


@app.put("/holdings/{ticker}", response_model=HoldingResponse)
async def update_holding(ticker: str, body: HoldingUpdateRequest) -> HoldingResponse:
    """Set the share count for a ticker after a payday buy.

    Replaces the existing value — pass the new total, not a delta.
    """
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    if body.shares < 0:
        raise HTTPException(status_code=422, detail="shares must be >= 0")
    await upsert_holding(ticker, body.shares)
    return HoldingResponse(ticker=ticker, shares=body.shares)


@app.get("/rebalancer/recommend", response_model=RebalancerResponse)
async def get_recommendations(contribution_cad: float) -> RebalancerResponse:
    """Return buy recommendations for a given CAD contribution amount.

    Fetches current holdings and latest prices from DB, then runs
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


@app.get("/rebalancer/timing", response_model=list[ExecutionWindow])
async def get_timing() -> list[ExecutionWindow]:
    """Return the best execution window for each tracked ETF."""
    return get_execution_windows()


@app.get("/summaries/{target_date}", response_model=list[SummaryResponse])
async def get_summary(target_date: date) -> list[SummaryResponse]:
    """Return daily spread summaries for all tickers on a given date."""
    rows = await fetch_daily_summary(str(target_date))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No summary data for {target_date}")
    return [SummaryResponse(**row) for row in rows]
