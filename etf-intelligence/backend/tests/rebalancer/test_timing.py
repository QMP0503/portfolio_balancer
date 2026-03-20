"""Tests for rebalancer/timing.py.

Stub behaviour only — no DB, no async.
"""

from rebalancer.timing import ExecutionWindow, get_execution_windows
from config.settings import TICKERS


def test_returns_one_window_per_ticker() -> None:
    """Default call returns a window for every tracked ticker."""
    windows = get_execution_windows()
    assert len(windows) == len(TICKERS)


def test_window_shape() -> None:
    """Each result is an ExecutionWindow with all fields populated."""
    windows = get_execution_windows()
    for w in windows:
        assert isinstance(w, ExecutionWindow)
        assert w.ticker
        assert w.best_start
        assert w.best_end
        assert w.note


def test_custom_ticker_list() -> None:
    """Passing a custom list returns only those tickers, in order."""
    subset = ["VFV.TO", "ZEM.TO"]
    windows = get_execution_windows(subset)
    assert [w.ticker for w in windows] == subset


def test_stub_note_present() -> None:
    """Stub note must signal that real analysis is pending."""
    windows = get_execution_windows()
    for w in windows:
        assert "pending" in w.note.lower()
