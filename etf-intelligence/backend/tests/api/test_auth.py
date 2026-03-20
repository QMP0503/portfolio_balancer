"""Tests for routers/auth.py — register and login endpoints."""

from fastapi.testclient import TestClient

_REGISTER_URL = "/auth/register"
_LOGIN_URL = "/auth/login"

_USER = {
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "password": "SecurePass1!",
}


def test_register_returns_token(client: TestClient) -> None:
    """Successful registration returns a JWT."""
    response = client.post(_REGISTER_URL, json=_USER)
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    """Registering the same email twice returns 409."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_REGISTER_URL, json=_USER)
    assert response.status_code == 409


def test_login_returns_token(client: TestClient) -> None:
    """Valid credentials return a JWT."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_LOGIN_URL, json={
        "email": _USER["email"],
        "password": _USER["password"],
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    """Wrong password returns 401."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_LOGIN_URL, json={
        "email": _USER["email"],
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    """Login with an unregistered email returns 401."""
    response = client.post(_LOGIN_URL, json={
        "email": "nobody@example.com",
        "password": "irrelevant",
    })
    assert response.status_code == 401


def test_login_remember_me_returns_token(client: TestClient) -> None:
    """remember_me=true returns a valid token (30-day expiry)."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_LOGIN_URL, json={
        "email": _USER["email"],
        "password": _USER["password"],
        "remember_me": True,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
