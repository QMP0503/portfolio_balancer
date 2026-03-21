"""seed_user.py — Create the initial admin user.

Run once after first `docker compose up`:
    docker compose exec backend python seed_user.py

Skips creation if the email already exists.
Credentials are read from env vars or fall back to defaults below.
"""

import asyncio
import os

from sqlalchemy import text

from auth import hash_password
from storage.database import AsyncSessionLocal

SEED_EMAIL = os.getenv("SEED_EMAIL", "admin@local.dev")
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "changeme")
SEED_FIRST = os.getenv("SEED_FIRST_NAME", "Admin")
SEED_LAST = os.getenv("SEED_LAST_NAME", "User")

_CHECK_SQL = text("SELECT id FROM users WHERE email = :email")
_INSERT_SQL = text("""
    INSERT INTO users (email, first_name, last_name, hashed_password)
    VALUES (:email, :first_name, :last_name, :hashed_password)
    RETURNING id
""")


async def seed() -> None:
    """Insert the seed user if they don't already exist."""
    async with AsyncSessionLocal() as session:
        existing = await session.execute(_CHECK_SQL, {"email": SEED_EMAIL})
        if existing.fetchone():
            print(f"User '{SEED_EMAIL}' already exists — skipping.")
            return

        result = await session.execute(_INSERT_SQL, {
            "email": SEED_EMAIL,
            "first_name": SEED_FIRST,
            "last_name": SEED_LAST,
            "hashed_password": hash_password(SEED_PASSWORD),
        })
        await session.commit()
        row = result.fetchone()

    print(f"Created user id={row.id} email={SEED_EMAIL}")
    print(f"Login with: {SEED_EMAIL} / {SEED_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
