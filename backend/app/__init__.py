"""Application package for NexusForge backend."""

# Lazy imports to avoid circular dependencies during Alembic migrations.
# Alembic's env.py imports from app.models.base which would otherwise
# trigger this __init__.py and cause a circular import chain:
#   app.models.base -> app.models -> app.__init__ -> app.main -> settings
# By using lazy import (on first attribute access), alembic can import
# from app.models.base without triggering the main app initialization.

def __getattr__(name):
    if name == "app":
        from .main import app
        return app
    if name == "get_settings":
        from .config.settings import get_settings
        return get_settings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
