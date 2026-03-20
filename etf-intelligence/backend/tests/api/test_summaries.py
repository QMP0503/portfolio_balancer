"""Tests for routers/summaries.py."""

from fastapi.testclient import TestClient


def test_summary_no_data_returns_404(client: TestClient, auth_cookies: dict) -> None:
    """404 returned when no summary exists for the requested date."""
    response = client.get("/summaries/2026-03-19", cookies=auth_cookies)
    assert response.status_code == 404


def test_summary_invalid_date_returns_422(client: TestClient, auth_cookies: dict) -> None:
    """Invalid date string returns 422."""
    response = client.get("/summaries/not-a-date", cookies=auth_cookies)
    assert response.status_code == 422


def test_summary_unauthenticated_returns_401(client: TestClient) -> None:
    """Request without cookie returns 401."""
    response = client.get("/summaries/2026-03-19")
    assert response.status_code == 401
