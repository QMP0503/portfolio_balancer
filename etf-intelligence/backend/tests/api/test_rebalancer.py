"""Tests for routers/rebalancer.py."""

from fastapi.testclient import TestClient


def test_timing_returns_windows(client: TestClient, auth_cookies: dict) -> None:
    """GET /rebalancer/timing returns one window per tracked ETF."""
    response = client.get("/rebalancer/timing", cookies=auth_cookies)
    assert response.status_code == 200
    windows = response.json()
    assert len(windows) == 4
    for w in windows:
        assert "ticker" in w
        assert "best_start" in w
        assert "best_end" in w


def test_recommend_no_allocations_returns_422(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """422 returned when portfolio has no allocations set."""
    response = client.get(
        f"/rebalancer/{portfolio_id}/recommend?contribution_cad=1200",
        cookies=auth_cookies,
    )
    assert response.status_code == 422


def test_recommend_no_price_data_returns_503(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """503 returned when quotes table has no data (market closed / fresh DB)."""
    # Set an allocation first so we get past the no-allocations check
    client.put(
        f"/portfolios/{portfolio_id}/allocations/VFV.TO",
        json={"target_pct": 100},
        cookies=auth_cookies,
    )
    response = client.get(
        f"/rebalancer/{portfolio_id}/recommend?contribution_cad=1200",
        cookies=auth_cookies,
    )
    assert response.status_code == 503


def test_recommend_negative_contribution_returns_422(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """Negative contribution amount returns 422."""
    response = client.get(
        f"/rebalancer/{portfolio_id}/recommend?contribution_cad=-500",
        cookies=auth_cookies,
    )
    assert response.status_code == 422


def test_recommend_zero_contribution_returns_422(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """Zero contribution amount returns 422."""
    response = client.get(
        f"/rebalancer/{portfolio_id}/recommend?contribution_cad=0",
        cookies=auth_cookies,
    )
    assert response.status_code == 422


def test_recommend_wrong_portfolio_returns_404(client: TestClient, auth_cookies: dict) -> None:
    """Portfolio not belonging to this user returns 404."""
    response = client.get(
        "/rebalancer/99999/recommend?contribution_cad=1200",
        cookies=auth_cookies,
    )
    assert response.status_code == 404


def test_rebalancer_unauthenticated_returns_401(client: TestClient) -> None:
    """Request without cookie returns 401."""
    response = client.get("/rebalancer/timing")
    assert response.status_code == 401
