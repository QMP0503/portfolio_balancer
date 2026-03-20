"""Tests for routers/quotes.py."""

from fastapi.testclient import TestClient


def test_latest_quotes_authenticated(client: TestClient, auth_cookies: dict) -> None:
    """Authenticated request returns 200 with a list (empty if no data)."""
    response = client.get("/quotes/latest", cookies=auth_cookies)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_latest_quotes_unauthenticated(client: TestClient) -> None:
    """Request without cookie returns 401."""
    response = client.get("/quotes/latest")
    assert response.status_code == 401


def test_latest_quotes_invalid_token(client: TestClient) -> None:
    """Request with a bad cookie value returns 401."""
    response = client.get("/quotes/latest", cookies={"access_token": "bad.token.here"})
    assert response.status_code == 401
