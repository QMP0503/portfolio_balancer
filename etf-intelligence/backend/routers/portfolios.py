"""routers/portfolios.py — Portfolio and allocation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from config.settings import TICKERS
from storage.database import (
    create_portfolio,
    fetch_portfolio_allocations,
    fetch_portfolios,
    upsert_portfolio_allocation,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


class PortfolioResponse(BaseModel):
    """A single user portfolio (one account)."""

    id: int
    account_name: str


class CreatePortfolioRequest(BaseModel):
    """Request body for creating a portfolio."""

    account_name: str


class AllocationResponse(BaseModel):
    """Target allocation for one ETF within a portfolio."""

    ticker: str
    target_pct: float
    goal: str | None


class AllocationUpdateRequest(BaseModel):
    """Request body for setting an ETF allocation."""

    target_pct: float
    goal: str | None = None


@router.get("", response_model=list[PortfolioResponse])
async def get_portfolios(user: dict = Depends(get_current_user)) -> list[PortfolioResponse]:
    """Return all portfolios belonging to the authenticated user."""
    rows = await fetch_portfolios(user["user_id"])
    return [PortfolioResponse(id=r["id"], account_name=r["account_name"]) for r in rows]


@router.post("", response_model=PortfolioResponse, status_code=201)
async def create_portfolio_endpoint(
    body: CreatePortfolioRequest,
    user: dict = Depends(get_current_user),
) -> PortfolioResponse:
    """Create a new portfolio for the authenticated user."""
    if not body.account_name.strip():
        raise HTTPException(status_code=422, detail="account_name cannot be empty")
    row = await create_portfolio(user["user_id"], body.account_name.strip())
    return PortfolioResponse(id=row["id"], account_name=row["account_name"])


@router.get("/{portfolio_id}/allocations", response_model=list[AllocationResponse])
async def get_allocations(
    portfolio_id: int,
    user: dict = Depends(get_current_user),
) -> list[AllocationResponse]:
    """Return ETF allocations for a portfolio."""
    await _assert_owns_portfolio(portfolio_id, user["user_id"])
    rows = await fetch_portfolio_allocations(portfolio_id)
    return [AllocationResponse(**r) for r in rows]


@router.put("/{portfolio_id}/allocations/{ticker}", response_model=AllocationResponse)
async def set_allocation(
    portfolio_id: int,
    ticker: str,
    body: AllocationUpdateRequest,
    user: dict = Depends(get_current_user),
) -> AllocationResponse:
    """Set the target allocation for one ETF in a portfolio."""
    await _assert_owns_portfolio(portfolio_id, user["user_id"])
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    if not (0 < body.target_pct <= 100):
        raise HTTPException(status_code=422, detail="target_pct must be between 0 and 100")
    await upsert_portfolio_allocation(portfolio_id, ticker, body.target_pct, body.goal)
    return AllocationResponse(ticker=ticker, target_pct=body.target_pct, goal=body.goal)


async def _assert_owns_portfolio(portfolio_id: int, user_id: int) -> None:
    """Raise 404 if the portfolio doesn't exist or belong to this user.

    Using 404 instead of 403 to avoid leaking whether a portfolio exists.

    Args:
        portfolio_id: Portfolio to check.
        user_id:      Authenticated user's ID.
    """
    rows = await fetch_portfolios(user_id)
    if not any(r["id"] == portfolio_id for r in rows):
        raise HTTPException(status_code=404, detail="Portfolio not found")
