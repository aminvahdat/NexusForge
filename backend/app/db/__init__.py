"""NexusForge data access layer — database service for Phase 2 foundation."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from typing import Optional, AsyncGenerator
from app.config.settings import get_settings
from app.models import Base, User, Project, Task, Artifact
import structlog

logger = structlog.get_logger()

# Global engine and session factory
_engine = None
_session_factory = None


def get_engine():
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        database_url = settings.database_url
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        _engine = create_async_engine(
            database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        logger.info("Database engine created", url=database_url.split('@')[0])
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: provide a database session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def init_database():
    """Initialize database by creating all tables and running migrations."""
    engine = get_engine()
    try:
        # Create all tables from models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
        
        # Run any pending Alembic migrations
        await run_migrations()
        
        # Verify database connectivity
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Database connectivity verified")
            else:
                raise RuntimeError("Database connectivity check failed")
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


async def run_migrations():
    """Run Alembic migrations if available."""
    try:
        import subprocess
        # Check if migrations directory exists
        import os
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if os.path.exists(migrations_dir):
            # Run alembic upgrade head
            result = subprocess.run(
                ['alembic', 'upgrade', 'head'],
                cwd=migrations_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Alembic migrations completed")
            else:
                logger.warning("Alembic migrations may have issues", output=result.stdout)
        else:
            logger.info("No migrations directory found (skipping)")
    except Exception as e:
        logger.warning("Migration system not available", error=str(e))


async def close_database():
    """Close database connections."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
    _session_factory = None


# Utility functions for common database operations
async def get_by_id(model, id: str, session: AsyncSession):
    """Generic get by ID function for all models."""
    if isinstance(id, str):
        from sqlalchemy.dialects.postgresql import UUID
        from uuid import UUID as PyUUID
        # Convert string to UUID
        id = PyUUID(id)
    
    result = await session.execute(text(f"SELECT * FROM {model.__tablename__} WHERE id = :id"), {'id': id})
    return result.scalar_one_or_none()


async def create_record(model, data: dict, session: AsyncSession):
    """Generic create record function."""
    record = model(**data)
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def update_record(record, data: dict, session: AsyncSession):
    """Generic update record function."""
    for key, value in data.items():
        if hasattr(record, key):
            setattr(record, key, value)
    
    await session.commit()
    await session.refresh(record)
    return record


async def delete_record(record, session: AsyncSession):
    """Generic delete record function."""
    await session.delete(record)
    await session.commit()


# Health checks
async def check_database_health():
    """Check database health."""
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


async def check_redis_health():
    """Check Redis health."""
    try:
        from app.services.redis import get_redis
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False


async def run_health_checks():
    """Run all health checks."""
    db_ok = await check_database_health()
    redis_ok = await check_redis_health()
    
    health_status = {
        'database': 'ok' if db_ok else 'error',
        'redis': 'ok' if redis_ok else 'error',
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if not db_ok or not redis_ok:
        raise RuntimeError(f"Health checks failed: {health_status}")
    
    logger.info("All health checks passed", status=health_status)
    return health_status