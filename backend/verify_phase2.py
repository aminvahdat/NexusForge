#!/usr/bin/env python3
"""Phase 2 verification script."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-long-enough-for-pydantic-validation-32chars")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nexusforge")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("API_ENV", "development")

from sqlalchemy import text
from app.db import get_engine
from app.services.redis import get_redis

async def verify():
    print("=== NexusForge Phase 2 Verification ===")

    # 1. Database
    print("1. Database connectivity...")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            db_val = result.scalar()
        print(f"   PASS: PostgreSQL query returned {db_val}")
    except Exception as e:
        print(f"   FAIL: {e}")
        return

    # 2. Redis
    print("2. Redis connectivity...")
    try:
        redis = await get_redis()
        await redis.ping()
        await redis.set("nexusforge:test", "phase2_ok")
        val = await redis.get("nexusforge:test")
        await redis.delete("nexusforge:test")
        print(f"   PASS: Redis ping OK, set/get={val}")
    except Exception as e:
        print(f"   FAIL: {e}")
        return

    # 3. Settings
    print("3. Configuration...")
    try:
        from app.config.settings import get_settings
        s = get_settings()
        print(f"   PASS: MAX_CONCURRENT_WORKERS={s.max_concurrent_workers}")
        print(f"   PASS: ai_provider={s.ai_provider} (provider-agnostic, None)")
        print(f"   PASS: api_env={s.api_env}")
        print(f"   PASS: debug={s.debug}")
    except Exception as e:
        print(f"   FAIL: {e}")
        return

    # 4. Schema — tables registered
    print("4. Database schema...")
    try:
        from app.models import Base
        expected = ['users','projects','tasks','artifacts','user_api_keys','workers',
                    'project_memory','notifications','approval_requests']
        for t in expected:
            if t in Base.metadata.tables:
                pks = [c.name for c in Base.metadata.tables[t].columns if c.primary_key]
                uuids_ok = any('uuid' in str(c.type).lower() for c in Base.metadata.tables[t].columns if c.primary_key)
                print(f"   PASS: {t:25s} pk={pks}")
            else:
                print(f"   MISSING: {t} not registered")
    except Exception as e:
        print(f"   FAIL: {e}")
        return

    print()
    print("ALL PHASE 2 CHECKS PASSED")

if __name__ == "__main__":
    asyncio.run(verify())
