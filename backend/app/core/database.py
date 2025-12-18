"""Database configuration and session management."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine with optimized connection pool settings
# SQLite doesn't support pool_size/max_overflow, so we conditionally set them
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connections before using
    "echo": False,  # Set to True for SQL logging in development
}

# Only set pool settings for non-SQLite databases
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_size": 10,  # Number of connections to maintain in pool
        "max_overflow": 20,  # Additional connections allowed beyond pool_size
    })
else:
    # SQLite-specific: use check_same_thread=False for async
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alias for backward compatibility
async_session_maker = AsyncSessionLocal

# Base class for ORM models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency function for getting database session.
    
    Yields an async database session that is automatically closed after use.
    Use this as a FastAPI dependency for database operations.
    
    Yields:
        AsyncSession: SQLAlchemy async database session.
        
    Example:
        ```python
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

