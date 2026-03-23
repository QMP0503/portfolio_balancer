"""storage/users.py — All queries for the users table."""

from sqlalchemy import text
from storage.database import AsyncSessionLocal


# Fetch a user's profile fields by id
_FETCH_PROFILE_SQL = text("""
    SELECT id, email, first_name, last_name
    FROM users
    WHERE id = :user_id
""")

# Update profile fields (email, first/last name)
_UPDATE_PROFILE_SQL = text("""
    UPDATE users
    SET email = :email, first_name = :first_name, last_name = :last_name
    WHERE id = :user_id
    RETURNING id, email, first_name, last_name
""")

# Update hashed_password only
_UPDATE_PASSWORD_SQL = text("""
    UPDATE users
    SET hashed_password = :hashed_password
    WHERE id = :user_id
""")

# Fetch hashed_password for current-password verification
_FETCH_PASSWORD_SQL = text("""
    SELECT hashed_password FROM users WHERE id = :user_id
""")


async def fetch_user_profile(user_id: int) -> dict | None:
    """Return profile fields for a user, or None if not found.

    Args:
        user_id: Primary key of the user.

    Returns:
        Dict with id, email, first_name, last_name or None.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(_FETCH_PROFILE_SQL, {"user_id": user_id})
        row = result.fetchone()
    return dict(row._mapping) if row else None


async def update_user_profile(user_id: int, email: str, first_name: str, last_name: str) -> dict:
    """Update a user's email and name, returning the updated row.

    Args:
        user_id: Primary key of the user.
        email: New email address.
        first_name: New first name.
        last_name: New last name.

    Returns:
        Updated dict with id, email, first_name, last_name.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(_UPDATE_PROFILE_SQL, {
            "user_id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        })
        await session.commit()
        row = result.fetchone()
    return dict(row._mapping)


async def fetch_hashed_password(user_id: int) -> str | None:
    """Return the stored hashed password for a user.

    Args:
        user_id: Primary key of the user.

    Returns:
        Hashed password string or None if user not found.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(_FETCH_PASSWORD_SQL, {"user_id": user_id})
        row = result.fetchone()
    return row.hashed_password if row else None


async def update_user_password(user_id: int, hashed_password: str) -> None:
    """Replace a user's hashed password.

    Args:
        user_id: Primary key of the user.
        hashed_password: New bcrypt hash to store.
    """
    async with AsyncSessionLocal() as session:
        await session.execute(_UPDATE_PASSWORD_SQL, {
            "user_id": user_id,
            "hashed_password": hashed_password,
        })
        await session.commit()
