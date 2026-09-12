from contextlib import asynccontextmanager
from datetime import datetime, timezone
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.db import init_database, close_database
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.execution import router as execution_router
from app.api.approval import router as approval_router
from app.api.worker import router as worker_controls_router
from app.api.settings import router as settings_router
from app.api.agents import router as agents_router
from app.api.artifact import router as artifact_router

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
    app.include_router(health_router, tags=["health"])
    app.include_router(health_router, prefix="/api", tags=["health"])
    # Authentication endpoints
    app.include_router(auth_router, tags=["auth"])
    app.include_router(auth_router, prefix="/api", tags=["auth"])

    # Project and task CRUD (Phase 2 foundation — auth added in Phase 3)
    app.include_router(tasks_router, tags=["projects", "tasks"])
    app.include_router(tasks_router, prefix="/api", tags=["projects", "tasks"])

    # Execution and real-time monitoring endpoints
    app.include_router(execution_router, tags=["execution", "realtime"])
    app.include_router(execution_router, prefix="/api", tags=["execution", "realtime"])
    # Approval Center (Phase 5.6)
    app.include_router(approval_router, tags=["approval", "security"])
    app.include_router(approval_router, prefix="/api", tags=["approval", "security"])
    # Worker controls (Phase 6)
    app.include_router(worker_controls_router, tags=["worker", "controls"])
    app.include_router(worker_controls_router, prefix="/api", tags=["worker", "controls"])
    # Settings and API Key management
    app.include_router(settings_router, tags=["settings"])
    app.include_router(settings_router, prefix="/api", tags=["settings"])
    # Agents Configuration & Prompt Customization
    app.include_router(agents_router, tags=["agents"])
    app.include_router(agents_router, prefix="/api", tags=["agents"])
    # Artifacts & Output Management
    app.include_router(artifact_router, tags=["artifacts"])
    app.include_router(artifact_router, prefix="/api", tags=["artifacts"])

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