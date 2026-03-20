"""
FastAPI application entry point for the ETF Portfolio Intelligence System.

Thin router only — registers APIRouters and manages app lifecycle.
No business logic, no response models, no SQL lives here.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingestion.scheduler import start_scheduler, stop_scheduler
from routers import quotes, holdings, rebalancer, summaries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""

    status: str
    version: str


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

app.include_router(quotes.router)
app.include_router(holdings.router)
app.include_router(rebalancer.router)
app.include_router(summaries.router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(status="ok", version="0.1.0")
