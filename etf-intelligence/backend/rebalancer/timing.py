"""rebalancer/timing.py — Best execution window per ETF.

Reads daily_summaries to find the hour of day with historically tightest
spreads per ticker. Currently stubbed — replace the query in
_fetch_best_hour() in Phase 7 once sufficient data has been collected.
"""

from pydantic import BaseModel

from config.settings import TICKERS


class ExecutionWindow(BaseModel):
    """Best time-of-day window to execute a buy for a given ETF."""

    ticker: str
    best_start: str  # 24h format, e.g. "11:00"
    best_end: str    # 24h format, e.g. "14:00"
    note: str        # human-readable context shown on dashboard


# Stub window returned for all tickers until real spread-by-hour data exists.
# Replace with a DB query in Phase 7 (spread.py analysis layer).
_STUB_WINDOW = ("11:00", "14:00")
_STUB_NOTE = "Estimated window — historical spread analysis pending"


def get_execution_windows(tickers: list[str] | None = None) -> list[ExecutionWindow]:
    """Return the best execution window for each requested ticker.

    Stubbed: always returns 11:00–14:00 ET regardless of ticker.
    Phase 7 will replace this with a query against daily_summaries
    grouped by hour to find the tightest historical spread window.

    Args:
        tickers: Tickers to return windows for. Defaults to all tracked tickers.

    Returns:
        One ExecutionWindow per ticker, ordered to match input list.
    """
    targets = tickers if tickers is not None else TICKERS
    start, end = _STUB_WINDOW

    return [
        ExecutionWindow(
            ticker=ticker,
            best_start=start,
            best_end=end,
            note=_STUB_NOTE,
        )
        for ticker in targets
    ]
