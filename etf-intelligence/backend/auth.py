"""auth.py — JWT creation, verification, and the get_current_user dependency.

All JWT logic lives here. Routers import get_current_user as a dependency.
No endpoint logic lives here.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import JWT_ALGORITHM, JWT_EXPIRY_DAYS, JWT_REMEMBER_ME_DAYS, JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(plain: str) -> str:
    """Return bcrypt hash of a plain-text password.

    Args:
        plain: Raw password string from the user.

    Returns:
        Bcrypt-hashed string safe to store in the database.
    """
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash.

    Args:
        plain:  Raw password to verify.
        hashed: Stored bcrypt hash from the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str, remember_me: bool = False) -> str:
    """Create a signed JWT for an authenticated user.

    Args:
        user_id:     Database ID of the user.
        email:       User's email address (included as a claim).
        remember_me: If True, token expires in 30 days instead of 1.

    Returns:
        Encoded JWT string ready to return to the client.
    """
    days = JWT_REMEMBER_ME_DAYS if remember_me else JWT_EXPIRY_DAYS
    expiry = datetime.now(timezone.utc) + timedelta(days=days)
    payload = {"sub": str(user_id), "email": email, "exp": expiry}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency — decode and validate the Bearer token.

    Raises HTTP 401 if the token is missing, expired, or invalid.

    Args:
        credentials: Injected by FastAPI from the Authorization header.

    Returns:
        Dict with keys: user_id (int), email (str).
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            raise JWTError("Missing claims")
        return {"user_id": int(user_id), "email": email}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
