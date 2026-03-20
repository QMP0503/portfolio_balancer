"""Tests for routers/rebalancer.py."""

from fastapi.testclient import TestClient


def test_timing_returns_windows(client: TestClient, auth_headers: dict) -> None:
    """GET /rebalancer/timing returns one window per tracked ETF."""
    response = client.get("/rebalancer/timing", headers=auth_headers)
    assert response.status_code == 200
    windows = response.json()
    assert len(windows) == 4
    for w in windows:
        assert "ticker" in w
        assert "best_start" in w
        assert "best_end" in w


def test_recommend_no_price_data_returns_503(client: TestClient, auth_headers: dict) -> None:
    """503 returned when quotes table has no data (market closed / fresh DB)."""
    response = client.get("/rebalancer/recommend?contribution_cad=1200", headers=auth_headers)
    assert response.status_code == 503


def test_recommend_negative_contribution_returns_422(client: TestClient, auth_headers: dict) -> None:
    """Negative contribution amount returns 422."""
    response = client.get("/rebalancer/recommend?contribution_cad=-500", headers=auth_headers)
    assert response.status_code == 422


def test_recommend_zero_contribution_returns_422(client: TestClient, auth_headers: dict) -> None:
    """Zero contribution amount returns 422."""
    response = client.get("/rebalancer/recommend?contribution_cad=0", headers=auth_headers)
    assert response.status_code == 422


def test_rebalancer_unauthenticated_returns_401(client: TestClient) -> None:
    """Request without token returns 401."""
    response = client.get("/rebalancer/timing")
    assert response.status_code == 401
