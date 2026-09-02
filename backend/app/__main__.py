"""Main entry point for NexusForge Phase 2 foundation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.config.settings import get_settings
from app.db import init_database
from app.services.redis import get_redis, close_redis
import asyncio
import structlog

logger = structlog.get_logger()


def main():
    """Main entry point for the application."""
    settings = get_settings()
    logger.info(
        "nexusforge.starting_phase2",
        version="0.1.0",
        env=settings.api_env,
        max_concurrent_workers=settings.max_concurrent_workers,
    )
    
    # Start database initialization
    logger.info("nexusforge.database.initializing")
    asyncio.run(init_database())
    
    # Test Redis connectivity
    logger.info("nexusforge.redis.testing")
    async def test_redis():
        redis = await get_redis()
        await redis.ping()
        logger.info("nexusforge.redis.connected")
    
    asyncio.run(test_redis())
    
    # Log configuration summary
    logger.info(
        "nexusforge.configuration_summary",
        database_url=settings.database_url,
        redis_url=settings.redis_url,
        ai_provider=settings.ai_provider,
        debug=settings.debug,
        log_level=settings.log_level,
    )
    
    # Log API endpoints available
    logger.info(
        "nexusforge.api_endpoints",
        root="GET /",
        health="GET /health",
        liveness="GET /health/liveness",
        readiness="GET /health/readiness",
        projects="GET /projects, POST /projects",
        tasks="GET /tasks, POST /tasks, PATCH /tasks/{id}, DELETE /tasks/{id}",
    )
    
    print("\n=== NexusForge Phase 2 Foundation Setup Complete ===")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"Database: {settings.database_url}")
    print(f"Redis: {settings.redis_url}")
    print(f"Max Concurrent Workers: {settings.max_concurrent_workers}")
    print(f"AI Provider: {settings.ai_provider} (provider-agnostic)")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print("\nAvailable API Endpoints:")
    print("  GET / - Root endpoint")
    print("  GET /health - Health check")
    print("  GET /health/liveness - Liveness probe")
    print("  GET /health/readiness - Readiness check")
    print("  GET /projects - List projects")
    print("  POST /projects - Create project")
    print("  GET /projects/{id} - Get project")
    print("  GET /projects/{id}/tasks - List project tasks")
    print("  GET /tasks - List tasks")
    print("  POST /tasks - Create task")
    print("  GET /tasks/{id} - Get task")
    print("  PATCH /tasks/{id} - Update task")
    print("  DELETE /tasks/{id} - Delete task")
    print("\nTest endpoints:")
    print("  curl http://localhost:8000/ -v")
    print("  curl http://localhost:8000/health -v")
    print("  curl http://localhost:8000/health/liveness -v")
    print("  curl http://localhost:8000/health/readiness -v")


if __name__ == "__main__":
    main()
