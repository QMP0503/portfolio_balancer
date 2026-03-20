"""Tests for routers/auth.py — register, login, and logout endpoints."""

from fastapi.testclient import TestClient

_REGISTER_URL = "/auth/register"
_LOGIN_URL = "/auth/login"
_LOGOUT_URL = "/auth/logout"

_USER = {
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "password": "SecurePass1!",
}


def test_register_sets_cookie_and_returns_user(client: TestClient) -> None:
    """Successful registration sets httpOnly cookie and returns user info."""
    response = client.post(_REGISTER_URL, json=_USER)
    assert response.status_code == 201
    assert "user_id" in response.json()
    assert response.json()["email"] == _USER["email"]
    assert "access_token" in response.cookies


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    """Registering the same email twice returns 409."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_REGISTER_URL, json=_USER)
    assert response.status_code == 409


def test_login_sets_cookie_and_returns_user(client: TestClient) -> None:
    """Valid credentials set httpOnly cookie and return user info."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_LOGIN_URL, json={
        "email": _USER["email"],
        "password": _USER["password"],
    })
    assert response.status_code == 200
    assert "user_id" in response.json()
    assert "access_token" in response.cookies


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


def test_login_remember_me_sets_cookie(client: TestClient) -> None:
    """remember_me=true still sets the auth cookie."""
    client.post(_REGISTER_URL, json=_USER)
    response = client.post(_LOGIN_URL, json={
        "email": _USER["email"],
        "password": _USER["password"],
        "remember_me": True,
    })
    assert response.status_code == 200
    assert "access_token" in response.cookies


def test_logout_clears_cookie(client: TestClient) -> None:
    """Logout endpoint clears the auth cookie."""
    client.post(_REGISTER_URL, json=_USER)
    login_response = client.post(_LOGIN_URL, json={
        "email": _USER["email"],
        "password": _USER["password"],
    })
    cookies = {"access_token": login_response.cookies.get("access_token")}
    response = client.post(_LOGOUT_URL, cookies=cookies)
    assert response.status_code == 204
