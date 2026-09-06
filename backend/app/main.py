from contextlib import asynccontextmanager
from datetime import datetime, timezone
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.db import init_database, close_database
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.api.execution import router as execution_router
from app.api.approval import router as approval_router
from app.api.worker import router as worker_controls_router

# Configure structured logging (no secrets)
def configure_logging() -> None:
    settings = get_settings()
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Application lifespan: startup → serve → shutdown."""
    settings = get_settings()
    configure_logging()
    logger = structlog.get_logger()
    logger.info(
        "nexusforge.starting",
        version="0.1.0",
        env=settings.api_env,
        max_concurrent_workers=settings.max_concurrent_workers,
    )
    try:
        await init_database()
        logger.info("nexusforge.database.ready")
    except Exception as e:
        logger.error("nexusforge.database.init_failed", error=str(e))
        raise
    yield
    await close_database()
    logger.info("nexusforge.shutdown.complete")

def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title="NexusForge API",
        description="Self-hosted multi-agent orchestration platform",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health and readiness endpoints
    app.include_router(health_router, prefix="/health", tags=["health"])

    # Project and task CRUD (Phase 2 foundation — auth added in Phase 3)
    app.include_router(tasks_router, tags=["projects", "tasks"])

    # Execution and real-time monitoring endpoints
    app.include_router(execution_router, prefix="/execution", tags=["execution", "realtime"])
    # Approval Center (Phase 5.6)
    app.include_router(approval_router, prefix="/approvals", tags=["approval", "security"])
    # Worker controls (Phase 6)
    app.include_router(worker_controls_router, prefix="/worker-controls", tags=["worker", "controls"])

    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": "NexusForge API",
            "version": "0.1.0",
            "status": "running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return app

app = create_app()