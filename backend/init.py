"""Main entry point for NexusForge backend."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.app.db import get_engine, init_database
from backend.app.config.settings import get_settings

def main() -> None:
    """Initialize NexusForge backend and check database connectivity."""
    settings = get_settings()
    print(f"=== NEXUSFORGE PHASE 2 INITIALIZATION ===")
    print(f"Environment: {settings.api_env}")
    print(f"Database: {settings.database_url.split('://')[-1].split('/')[0]}")
    print(f"Max concurrent workers: {settings.max_concurrent_workers}")
    print(f"AI provider: {settings.ai_provider}")
    print()

    # Initialize database
    print("Initializing database...")
    engine = init_database()
    print("✓ Database initialized")

    # Check database connectivity
    print("\nChecking database connectivity...")
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database query successful")
            print(f"  Result: {result.scalar()}")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return

    # Check tables
    print("\nChecking database schema...")
    from backend.app.models import Base
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✓ Found {len(tables)} tables: {', '.join(sorted(tables))}")

    # Check required tables
    required_tables = {"users", "projects", "tasks", "artifacts", "workers"}
    missing = required_tables - set(tables)
    if missing:
        print(f"✗ Missing required tables: {', '.join(sorted(missing))}")
        return
    else:
        print("✓ All required tables present")

    print("\n=== PHASE 2 INITIALIZATION COMPLETE ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)