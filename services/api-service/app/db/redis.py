"""
Redis async connection for caching and session management.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

# ── Client ──
_redis_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Get the Redis client instance with connection pooling."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_pool


# ── Lifecycle ──


async def init_redis() -> None:
    """Initialize Redis connection and verify connectivity."""
    client = get_redis()
    await client.ping()


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


async def check_redis_health() -> bool:
    """Check Redis connectivity for health endpoints."""
    try:
        client = get_redis()
        return await client.ping()
    except Exception:
        return False
