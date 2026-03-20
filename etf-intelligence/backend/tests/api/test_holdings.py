"""Tests for routers/holdings.py."""

from fastapi.testclient import TestClient


def test_get_holdings_returns_list(client: TestClient, auth_headers: dict) -> None:
    """Authenticated GET returns a list (empty if no holdings set)."""
    response = client.get("/holdings", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_holding_updates_shares(client: TestClient, auth_headers: dict) -> None:
    """PUT sets share count and returns the updated holding."""
    response = client.put("/holdings/VFV.TO", json={"shares": 10}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["ticker"] == "VFV.TO"
    assert response.json()["shares"] == 10


def test_put_holding_reflects_in_get(client: TestClient, auth_headers: dict) -> None:
    """Share count updated via PUT is visible in GET /holdings."""
    client.put("/holdings/VCN.TO", json={"shares": 25}, headers=auth_headers)
    holdings = client.get("/holdings", headers=auth_headers).json()
    tickers = {h["ticker"]: h["shares"] for h in holdings}
    assert tickers["VCN.TO"] == 25


def test_put_holding_unknown_ticker_returns_404(client: TestClient, auth_headers: dict) -> None:
    """Unknown ticker returns 404."""
    response = client.put("/holdings/FAKE.TO", json={"shares": 5}, headers=auth_headers)
    assert response.status_code == 404


def test_put_holding_negative_shares_returns_422(client: TestClient, auth_headers: dict) -> None:
    """Negative share count returns 422."""
    response = client.put("/holdings/VFV.TO", json={"shares": -1}, headers=auth_headers)
    assert response.status_code == 422


def test_holdings_unauthenticated_returns_401(client: TestClient) -> None:
    """Request without token returns 401."""
    response = client.get("/holdings")
    assert response.status_code == 401
