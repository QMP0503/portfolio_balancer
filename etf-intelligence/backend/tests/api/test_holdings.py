"""Tests for routers/holdings.py — portfolio-scoped holdings endpoints."""

from fastapi.testclient import TestClient


def test_get_holdings_returns_list(client: TestClient, auth_cookies: dict, portfolio_id: int) -> None:
    """Authenticated GET returns a list (empty if no holdings set)."""
    response = client.get(f"/portfolios/{portfolio_id}/holdings", cookies=auth_cookies)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_holding_updates_shares(client: TestClient, auth_cookies: dict, portfolio_id: int) -> None:
    """PUT sets share count and returns the updated holding."""
    response = client.put(
        f"/portfolios/{portfolio_id}/holdings/VFV.TO",
        json={"shares": 10},
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    assert response.json()["ticker"] == "VFV.TO"
    assert response.json()["shares"] == 10


def test_put_holding_reflects_in_get(client: TestClient, auth_cookies: dict, portfolio_id: int) -> None:
    """Share count updated via PUT is visible in GET holdings."""
    client.put(
        f"/portfolios/{portfolio_id}/holdings/VCN.TO",
        json={"shares": 25},
        cookies=auth_cookies,
    )
    holdings = client.get(f"/portfolios/{portfolio_id}/holdings", cookies=auth_cookies).json()
    tickers = {h["ticker"]: h["shares"] for h in holdings}
    assert tickers["VCN.TO"] == 25


def test_put_holding_unknown_ticker_returns_404(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """Unknown ticker returns 404."""
    response = client.put(
        f"/portfolios/{portfolio_id}/holdings/FAKE.TO",
        json={"shares": 5},
        cookies=auth_cookies,
    )
    assert response.status_code == 404


def test_put_holding_negative_shares_returns_422(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """Negative share count returns 422."""
    response = client.put(
        f"/portfolios/{portfolio_id}/holdings/VFV.TO",
        json={"shares": -1},
        cookies=auth_cookies,
    )
    assert response.status_code == 422


def test_holdings_wrong_portfolio_returns_404(client: TestClient, auth_cookies: dict) -> None:
    """Portfolio not belonging to this user returns 404."""
    response = client.get("/portfolios/99999/holdings", cookies=auth_cookies)
    assert response.status_code == 404


def test_holdings_unauthenticated_returns_401(client: TestClient) -> None:
    """Request without cookie returns 401."""
    response = client.get("/portfolios/1/holdings")
    assert response.status_code == 401
