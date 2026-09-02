"""FastAPI health endpoints for NexusForge."""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.db import get_db_session
from app.services.redis import get_redis

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health", summary="Health check endpoint")
async def health_check(db_session: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Health check endpoint to verify system is operational."""
    try:
        # Check database connection
        result = await db_session.execute(text("SELECT 1"))
        db_ok = result.scalar() is not None

        # Check redis connection
        redis = get_redis()
        await redis.ping()
        redis_ok = True

        if db_ok and redis_ok:
            return {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "ok",
                "redis": "ok",
            }
        else:
            raise HTTPException(status_code=500, detail="Database connection failed")
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.get("/health/liveness", summary="Liveness probe")
async def liveness_check() -> Dict[str, str]:
    """Liveness probe for container orchestration."""
    return {"status": "alive"}


@router.get("/health/readiness", summary="Readiness check")
async def readiness_check(
    db_session: AsyncSession = Depends(get_db_session)
) -> Dict[str, str]:
    """Readiness check to verify dependencies are available."""
    try:
        # Check database
        await db_session.execute(text("SELECT 1"))

        # Check redis
        redis = get_redis()
        await redis.ping()

        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")