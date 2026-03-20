"""routers/auth.py — Login and registration endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text

from auth import create_access_token, hash_password, verify_password
from storage.database import AsyncSessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])


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


class TokenResponse(BaseModel):
    """Returned on successful login or registration."""

    access_token: str
    token_type: str = "bearer"


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


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest) -> TokenResponse:
    """Create a new account and return a JWT."""
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
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate and return a JWT."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(_FETCH_USER_SQL, {"email": body.email})
        user = result.fetchone()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        remember_me=body.remember_me,
    )
    return TokenResponse(access_token=token)
