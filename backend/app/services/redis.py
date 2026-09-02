"""Redis service for NexusForge — queue, caching, and pub/sub."""

from redis import asyncio as aioredis  # type: ignore[attr-defined]
from redis.asyncio import Redis  # type: ignore[attr-defined]
from app.config.settings import get_settings
from typing import Optional
import structlog

logger = structlog.get_logger()

_redis: Optional[Redis] = None


async def get_redis() -> Redis:
    """Get or create the Redis connection pool."""
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        logger.info("Redis connection created", url=settings.redis_url.split('@')[-1].split('/')[0])
    return _redis


async def close_redis():
    """Close the Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed")


# ── Task Queue ────────────────────────────────────────────────────────────────

TASK_QUEUE = "nexusforge:task_queue"
WORKER_QUEUE = "nexusforge:worker_queue"
STATUS_CHANNEL = "nexusforge:status_updates"


async def enqueue_task(task_id: str) -> None:
    """Push a task ID onto the queue."""
    redis = await get_redis()
    await redis.lpush(TASK_QUEUE, task_id)


async def dequeue_task(timeout: int = 5) -> Optional[str]:
    """Blocking pop from the task queue."""
    redis = await get_redis()
    result = await redis.brpop(TASK_QUEUE, timeout=timeout)
    if result:
        _, task_id = result
        return task_id
    return None


async def get_queue_length() -> int:
    """Return number of pending tasks."""
    redis = await get_redis()
    return await redis.llen(TASK_QUEUE)


# ── Worker Pool State ────────────────────────────────────────────────────────

WORKER_STATE_KEY = "nexusforge:workers:active"
WORKER_LOCK_PREFIX = "nexusforge:worker_lock:"


async def register_worker(worker_id: str) -> bool:
    """Register a worker in Redis (heartbeat)."""
    redis = await get_redis()
    await redis.hset(WORKER_STATE_KEY, worker_id, "idle")
    await redis.expire(WORKER_STATE_KEY, 300)
    return True


async def unregister_worker(worker_id: str) -> None:
    """Remove a worker from Redis."""
    redis = await get_redis()
    await redis.hdel(WORKER_STATE_KEY, worker_id)
    await redis.delete(f"{WORKER_LOCK_PREFIX}{worker_id}")


async def get_active_workers() -> list[str]:
    """Get list of active worker IDs."""
    redis = await get_redis()
    return await redis.hkeys(WORKER_STATE_KEY)


async def acquire_worker_lock(worker_id: str, ttl: int = 30) -> bool:
    """Acquire an exclusive lock for a worker."""
    redis = await get_redis()
    key = f"{WORKER_LOCK_PREFIX}{worker_id}"
    return await redis.set(key, "1", nx=True, ex=ttl)


async def release_worker_lock(worker_id: str) -> None:
    """Release the worker lock."""
    redis = await get_redis()
    await redis.delete(f"{WORKER_LOCK_PREFIX}{worker_id}")


# ── Pub/Sub ─────────────────────────────────────────────────────────────────

async def publish_status(channel: str, message: dict) -> None:
    """Publish a status update to a channel."""
    redis = await get_redis()
    import json
    await redis.publish(channel, json.dumps(message))


# ── Cache ───────────────────────────────────────────────────────────────────

CACHE_TTL = 300  # seconds


async def cache_set(key: str, value: str, ttl: int = CACHE_TTL) -> None:
    redis = await get_redis()
    await redis.setex(f"nexusforge:cache:{key}", ttl, value)


async def cache_get(key: str) -> Optional[str]:
    redis = await get_redis()
    return await redis.get(f"nexusforge:cache:{key}")


async def cache_delete(key: str) -> None:
    redis = await get_redis()
    await redis.delete(f"nexusforge:cache:{key}")
