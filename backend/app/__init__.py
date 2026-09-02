"""Application package for NexusForge backend."""
from .main import app
from .config.settings import get_settings

# Clean import chain verification
try:
    from app.config import Settings, get_settings as get_config
    from app.db import get_engine, get_session_factory, init_database, close_database
    from app.services import redis
except ImportError:
    pass  # Packages may not be available in some contexts
