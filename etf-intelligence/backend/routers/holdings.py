"""routers/holdings.py — Holdings read and update endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config.settings import TICKERS
from routers.portfolios import _assert_owns_portfolio
from storage.database import fetch_holdings, upsert_holding

router = APIRouter(prefix="/portfolios", tags=["holdings"])


class HoldingResponse(BaseModel):
    """Current share count for a single ETF in a portfolio."""

    ticker: str
    shares: float


class HoldingUpdateRequest(BaseModel):
    """Request body for updating a holding."""

    shares: float


@router.get("/{portfolio_id}/holdings", response_model=list[HoldingResponse])
async def get_holdings(
    portfolio_id: int,
    user: dict = Depends(get_current_user),
) -> list[HoldingResponse]:
    """Return current share counts for all ETFs in a portfolio."""
    await _assert_owns_portfolio(portfolio_id, user["user_id"])
    rows = await fetch_holdings(portfolio_id)
    return [HoldingResponse(ticker=r["ticker"], shares=r["shares"]) for r in rows]


@router.put("/{portfolio_id}/holdings/{ticker}", response_model=HoldingResponse)
async def update_holding(
    portfolio_id: int,
    ticker: str,
    body: HoldingUpdateRequest,
    user: dict = Depends(get_current_user),
) -> HoldingResponse:
    """Set the share count for a ticker after a payday buy.

    Replaces the existing value — pass the new total, not a delta.
    """
    await _assert_owns_portfolio(portfolio_id, user["user_id"])
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    if body.shares < 0:
        raise HTTPException(status_code=422, detail="shares must be >= 0")
    await upsert_holding(portfolio_id, ticker, body.shares)
    return HoldingResponse(ticker=ticker, shares=body.shares)
