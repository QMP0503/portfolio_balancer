"""routers/quotes.py — Market quote endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from storage.quotes import fetch_latest_quotes

router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuoteResponse(BaseModel):
    """Latest market quote for a single ETF."""

    ticker: str
    bid: float | None
    ask: float | None
    spread: float | None
    price: float | None
    volume: int | None


@router.get("/latest", response_model=list[QuoteResponse])
async def get_latest_quotes(_: dict = Depends(get_current_user)) -> list[QuoteResponse]:
    """Return the most recent stored quote for each tracked ETF."""
    rows = await fetch_latest_quotes()
    return [QuoteResponse(**row) for row in rows]
