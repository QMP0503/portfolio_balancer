"""routers/summaries.py — Daily spread summary endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from storage.database import fetch_daily_summary

router = APIRouter(prefix="/summaries", tags=["summaries"])


class SummaryResponse(BaseModel):
    """Daily spread summary for a single ETF."""

    date: date
    ticker: str
    avg_spread: float | None
    min_spread: float | None
    max_spread: float | None
    volatility_score: float | None


@router.get("/{target_date}", response_model=list[SummaryResponse])
async def get_summary(target_date: date, _: dict = Depends(get_current_user)) -> list[SummaryResponse]:
    """Return daily spread summaries for all tickers on a given date."""
    rows = await fetch_daily_summary(target_date)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No summary data for {target_date}")
    return [SummaryResponse(**row) for row in rows]
