"""
Async Database Engine & Session Management
Uses SQLAlchemy 2.0 async engine with connection pooling.
"""

from collections.abc import AsyncGenerator
from typing import Any

from app.config import settings
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


# ─── Declarative Base ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ─── Engine ───────────────────────────────────────────────────────────────────
def _make_engine():
    """Create async engine with appropriate settings for env."""
    kwargs: dict[str, Any] = {
        "echo": settings.DB_ECHO,
        "future": True,
        "prepared_statement_cache_size": 0,
    }

    # Use NullPool for test environments (avoids connection pool issues)
    if settings.TESTING:
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 3600

    return create_async_engine(settings.DATABASE_URL, **kwargs)


engine = _make_engine()

# ─── Session Factory ──────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ─── Dependency ───────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a database session, ensures close on exit."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── DB Init ──────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Create all tables (dev only — use Alembic in production)."""
    async with engine.begin() as conn:
        import app.models  # noqa: F401 — ensure models are registered
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose engine connection pool gracefully."""
    await engine.dispose()
