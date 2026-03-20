"""routers/auth.py — Login, registration, and logout endpoints."""

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from auth import create_access_token, hash_password, verify_password
from config.settings import JWT_EXPIRY_DAYS, JWT_REMEMBER_ME_DAYS
from storage.database import AsyncSessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie name used consistently across set/clear operations
_COOKIE_NAME = "access_token"


class RegisterRequest(BaseModel):
    """Request body for creating a new account."""

    email: EmailStr
    first_name: str
    last_name: str
    password: str


class LoginRequest(BaseModel):
    """Request body for logging in."""

    email: EmailStr
    password: str
    remember_me: bool = False


class AuthResponse(BaseModel):
    """Returned on successful login or registration."""

    user_id: int
    email: str


# Fetch a user row by email — used by both login and register
_FETCH_USER_SQL = text("""
    SELECT id, email, hashed_password, is_active
    FROM users
    WHERE email = :email
""")

# Insert a new user row
_INSERT_USER_SQL = text("""
    INSERT INTO users (email, first_name, last_name, hashed_password)
    VALUES (:email, :first_name, :last_name, :hashed_password)
    RETURNING id, email
""")


def _set_auth_cookie(response: Response, token: str, remember_me: bool = False) -> None:
    """Set the httpOnly auth cookie on the response.

    Args:
        response:    FastAPI response object to attach the cookie to.
        token:       Encoded JWT string.
        remember_me: If True, cookie max_age matches the 30-day token lifetime.
    """
    max_age = (JWT_REMEMBER_ME_DAYS if remember_me else JWT_EXPIRY_DAYS) * 86400
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="strict",
        secure=False,  # set True in production behind HTTPS
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response) -> AuthResponse:
    """Create a new account, set auth cookie, and return basic user info."""
    async with AsyncSessionLocal() as session:
        existing = await session.execute(_FETCH_USER_SQL, {"email": body.email})
        if existing.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered")

        result = await session.execute(_INSERT_USER_SQL, {
            "email": body.email,
            "first_name": body.first_name,
            "last_name": body.last_name,
            "hashed_password": hash_password(body.password),
        })
        await session.commit()
        row = result.fetchone()

    token = create_access_token(user_id=row.id, email=row.email)
    _set_auth_cookie(response, token)
    return AuthResponse(user_id=row.id, email=row.email)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, response: Response) -> AuthResponse:
    """Authenticate, set auth cookie, and return basic user info."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(_FETCH_USER_SQL, {"email": body.email})
        user = result.fetchone()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(user_id=user.id, email=user.email, remember_me=body.remember_me)
    _set_auth_cookie(response, token, remember_me=body.remember_me)
    return AuthResponse(user_id=user.id, email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear the auth cookie to log the user out."""
    response.delete_cookie(key=_COOKIE_NAME, httponly=True, samesite="strict")
