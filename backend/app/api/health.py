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
        db_status = await get_database_status(db_session)
        db_ok = db_status == "healthy"

        # Check redis connection
        redis = await get_redis()
        await redis.ping()
        redis_ok = True

        if db_ok and redis_ok:
            return {
                "status": "healthy",
                "api": "healthy",
                "database": "healthy",
                "redis": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            details = []
            if not db_ok:
                details.append("Database connection failed")
            if not redis_ok:
                details.append("Redis connection failed")
            raise HTTPException(status_code=503, detail=f"Service unhealthy: {', '.join(details)}")

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@router.get("/health/liveness", summary="Liveness probe")
async def liveness_check() -> Dict[str, str]:
    """Liveness probe for container orchestration."""
    return {"status": "alive"}

@router.get("/health/readiness", summary="Readiness check")
async def readiness_check(db_session: AsyncSession = Depends(get_db_session)) -> Dict[str, str]:
    """Readiness check to verify dependencies are available."""
    try:
        # Check database
        await get_database_status(db_session)
        db_ok = True

        # Check redis
        redis = await get_redis()
        await redis.ping()
        redis_ok = True

        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

# Database status helper
async def get_database_status(db_session: AsyncSession) -> str:
    """Check database connection status."""
    try:
        await db_session.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        return "unhealthy"
