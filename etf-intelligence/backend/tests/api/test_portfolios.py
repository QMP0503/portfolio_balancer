"""Tests for routers/portfolios.py — portfolio and allocation endpoints."""

from fastapi.testclient import TestClient


def test_create_portfolio_returns_201(client: TestClient, auth_cookies: dict) -> None:
    """Creating a portfolio returns 201 with id and account_name."""
    response = client.post("/portfolios", json={"account_name": "TFSA"}, cookies=auth_cookies)
    assert response.status_code == 201
    assert response.json()["account_name"] == "TFSA"
    assert "id" in response.json()


def test_get_portfolios_returns_list(client: TestClient, auth_cookies: dict) -> None:
    """GET /portfolios returns a list of the user's portfolios."""
    client.post("/portfolios", json={"account_name": "TFSA"}, cookies=auth_cookies)
    client.post("/portfolios", json={"account_name": "FHSA"}, cookies=auth_cookies)
    response = client.get("/portfolios", cookies=auth_cookies)
    assert response.status_code == 200
    names = [p["account_name"] for p in response.json()]
    assert "TFSA" in names
    assert "FHSA" in names


def test_create_portfolio_empty_name_returns_422(client: TestClient, auth_cookies: dict) -> None:
    """Empty account_name returns 422."""
    response = client.post("/portfolios", json={"account_name": "  "}, cookies=auth_cookies)
    assert response.status_code == 422


def test_set_allocation_returns_200(client: TestClient, auth_cookies: dict, portfolio_id: int) -> None:
    """PUT allocation returns the saved allocation."""
    response = client.put(
        f"/portfolios/{portfolio_id}/allocations/VFV.TO",
        json={"target_pct": 40.0, "goal": "S&P 500 exposure"},
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    assert response.json()["ticker"] == "VFV.TO"
    assert response.json()["target_pct"] == 40.0
    assert response.json()["goal"] == "S&P 500 exposure"


def test_get_allocations_reflects_put(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """Allocation set via PUT is visible in GET allocations."""
    client.put(
        f"/portfolios/{portfolio_id}/allocations/HXQ.TO",
        json={"target_pct": 35.0},
        cookies=auth_cookies,
    )
    response = client.get(f"/portfolios/{portfolio_id}/allocations", cookies=auth_cookies)
    assert response.status_code == 200
    tickers = {a["ticker"]: a["target_pct"] for a in response.json()}
    assert tickers["HXQ.TO"] == 35.0


def test_set_allocation_unknown_ticker_returns_404(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """Unknown ticker returns 404."""
    response = client.put(
        f"/portfolios/{portfolio_id}/allocations/FAKE.TO",
        json={"target_pct": 10.0},
        cookies=auth_cookies,
    )
    assert response.status_code == 404


def test_set_allocation_out_of_range_returns_422(
    client: TestClient, auth_cookies: dict, portfolio_id: int
) -> None:
    """target_pct outside (0, 100] returns 422."""
    response = client.put(
        f"/portfolios/{portfolio_id}/allocations/VFV.TO",
        json={"target_pct": 0},
        cookies=auth_cookies,
    )
    assert response.status_code == 422


def test_wrong_portfolio_returns_404(client: TestClient, auth_cookies: dict) -> None:
    """Portfolio not owned by this user returns 404."""
    response = client.get("/portfolios/99999/allocations", cookies=auth_cookies)
    assert response.status_code == 404


def test_portfolios_unauthenticated_returns_401(client: TestClient) -> None:
    """Request without cookie returns 401."""
    response = client.get("/portfolios")
    assert response.status_code == 401
