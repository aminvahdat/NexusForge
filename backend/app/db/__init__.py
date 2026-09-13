"""Database configuration for NexusForge."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import get_settings

settings = get_settings()

import os
import sys
from sqlalchemy.pool import NullPool

is_test = "pytest" in sys.modules or os.environ.get("TESTING") == "1"

if "sqlite" in settings.database_url:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=NullPool if is_test else None,
    )
else:
    if is_test:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            poolclass=NullPool,
        )
    else:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10,
        )

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_engine():
    return engine


def get_session_factory():
    return async_session


from app.models.base import Base


async def get_db_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_database() -> None:
    import app.models  # Ensure all models are registered on Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    await engine.dispose()