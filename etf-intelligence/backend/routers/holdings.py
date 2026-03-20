"""routers/holdings.py — Holdings read and update endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config.settings import TICKERS
from storage.database import fetch_holdings, upsert_holding

router = APIRouter(prefix="/holdings", tags=["holdings"])


class HoldingResponse(BaseModel):
    """Current share count for a single ETF."""

    ticker: str
    shares: float


class HoldingUpdateRequest(BaseModel):
    """Request body for updating a holding."""

    shares: float


@router.get("", response_model=list[HoldingResponse])
async def get_holdings(_: dict = Depends(get_current_user)) -> list[HoldingResponse]:
    """Return current share counts for all tracked ETFs."""
    rows = await fetch_holdings()
    return [HoldingResponse(**row) for row in rows]


@router.put("/{ticker}", response_model=HoldingResponse)
async def update_holding(ticker: str, body: HoldingUpdateRequest, _: dict = Depends(get_current_user)) -> HoldingResponse:
    """Set the share count for a ticker after a payday buy.

    Replaces the existing value — pass the new total, not a delta.
    """
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    if body.shares < 0:
        raise HTTPException(status_code=422, detail="shares must be >= 0")
    await upsert_holding(ticker, body.shares)
    return HoldingResponse(ticker=ticker, shares=body.shares)
