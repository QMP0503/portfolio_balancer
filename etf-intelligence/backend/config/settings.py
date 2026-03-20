"""
Module-level configuration constants for the ETF Portfolio Intelligence System.

Loads environment variables from .env via python-dotenv.
All other modules import from here — no hardcoded values elsewhere.
"""

import os
from datetime import time

from dotenv import load_dotenv

load_dotenv()

# ETFs being tracked
TICKERS: list[str] = ["HXQ.TO", "VFV.TO", "VCN.TO", "ZEM.TO"]

# Target allocation percentages (must sum to 100)
TARGET_ALLOCATIONS: dict[str, float] = {
    "HXQ.TO": 40.0,
    "VFV.TO": 35.0,
    "VCN.TO": 15.0,
    "ZEM.TO": 10.0,
}

# Market hours (Toronto Stock Exchange)
MARKET_OPEN: str = "09:30"
MARKET_CLOSE: str = "16:00"
TIMEZONE: str = "America/Toronto"

# How often the ingestion scheduler runs
FETCH_INTERVAL_SECONDS: int = 60

# JWT authentication
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_DAYS: int = 1        # default token lifetime
JWT_REMEMBER_ME_DAYS: int = 30  # lifetime when user selects "remember me"

# Database — built from individual env vars if DATABASE_URL is not set directly
DATABASE_URL: str = os.getenv("DATABASE_URL") or (
    "postgresql+asyncpg://"
    f"{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'db')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'etf_db')}"
)
