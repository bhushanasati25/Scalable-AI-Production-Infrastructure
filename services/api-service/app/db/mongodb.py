"""
MongoDB async connection with Motor driver.
Connection pooling and collection abstraction.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

settings = get_settings()

# ── Client ──
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Get the MongoDB client instance."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongo_url,
            maxPoolSize=settings.mongo_max_pool_size,
            minPoolSize=settings.mongo_min_pool_size,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True,
        )
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance."""
    global _database
    if _database is None:
        client = get_mongo_client()
        _database = client[settings.mongo_db]
    return _database


# ── Collection Accessors ──

def get_inference_logs_collection():
    """Get the inference_logs collection."""
    return get_mongo_db()["inference_logs"]


def get_audit_trail_collection():
    """Get the audit_trail collection."""
    return get_mongo_db()["audit_trail"]


def get_system_metrics_collection():
    """Get the system_metrics collection."""
    return get_mongo_db()["system_metrics"]


# ── Lifecycle ──

async def init_mongo() -> None:
    """Initialize MongoDB connection and verify connectivity."""
    db = get_mongo_db()
    # Verify connectivity with a ping
    await db.command("ping")


async def close_mongo() -> None:
    """Close MongoDB connection."""
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None


async def check_mongo_health() -> bool:
    """Check MongoDB connectivity for health endpoints."""
    try:
        db = get_mongo_db()
        await db.command("ping")
        return True
    except Exception:
        return False
