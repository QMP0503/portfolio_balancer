"""storage/database.py — Async database engine and session factory.

Only connection infrastructure lives here.
All query functions live in their domain modules:
  storage/quotes.py, storage/portfolios.py, storage/holdings.py, storage/summaries.py
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import DATABASE_URL

# Ensure the URL uses the asyncpg driver — docker-compose injects a plain postgresql:// URL
_async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_async_url, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for use with FastAPI Depends."""
    async with AsyncSessionLocal() as session:
        yield session
