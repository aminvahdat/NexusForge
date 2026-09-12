"""Database configuration for NexusForge."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import get_settings

settings = get_settings()

if "sqlite" in settings.database_url:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
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

    try:
        import bcrypt
        from app.models.user import User
        from app.models import Project
        from sqlalchemy import select
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == "admin@nexusforge.io"))
            user = result.scalar_one_or_none()
            if not user:
                hash_pw = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
                user = User(
                    email="admin@nexusforge.io",
                    username="admin",
                    password_hash=hash_pw,
                    is_active=True,
                    is_superuser=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            proj_res = await session.execute(select(Project).limit(1))
            if not proj_res.scalar_one_or_none():
                proj = Project(
                    name="NexusForge Core",
                    description="Autonomous Multi-Agent Orchestration Platform",
                    status="active",
                    owner_id=user.id,
                )
                session.add(proj)
                await session.commit()
    except Exception as err:
        import structlog
        structlog.get_logger().warning("admin_seed_check_warning", error=str(err))


async def close_database() -> None:
    await engine.dispose()