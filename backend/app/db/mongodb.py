"""MongoDB (Motor async) client singleton with connection retry.

See DDD 12.4: retry 3x with 2s intervals on connection failure.
"""
from __future__ import annotations

import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config import get_settings

logger = logging.getLogger(__name__)

COMPETENCY_MATRIX = "competency_matrix"
COURSE_CATALOG = "course_catalog"

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo(max_retries: int = 3, retry_interval: float = 2.0) -> AsyncIOMotorDatabase:
    """Establish the Mongo connection (idempotent). Retries per DDD 12.4."""
    global _client, _db
    if _db is not None:
        return _db

    settings = get_settings()
    last_err: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                uuidRepresentation="standard",
            )
            # Force a round-trip to verify connectivity.
            await client.admin.command("ping")
            _client = client
            _db = client[settings.mongodb_db_name]
            logger.info("MongoDB connected (db=%s)", settings.mongodb_db_name)
            await _ensure_indexes(_db)
            return _db
        except PyMongoError as exc:  # pragma: no cover - network dependent
            last_err = exc
            logger.warning(
                "MongoDB connection attempt %d/%d failed: %s", attempt, max_retries, exc
            )
            if attempt < max_retries:
                await asyncio.sleep(retry_interval)

    raise RuntimeError(f"Database unavailable after {max_retries} attempts: {last_err}")


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes described in DDD 3.1.3 and 3.2.3 (idempotent)."""
    try:
        cm = db[COMPETENCY_MATRIX]
        await cm.create_index("role_slug", unique=True)
        await cm.create_index("role_name", unique=True)
        await cm.create_index("skills.skill_name")
        await cm.create_index("skills.category")

        cc = db[COURSE_CATALOG]
        await cc.create_index("course_id", unique=True)
        await cc.create_index("skill_tags")
        await cc.create_index("primary_category")
        await cc.create_index("level_numeric")
        await cc.create_index("is_embedded")
    except PyMongoError as exc:  # pragma: no cover
        logger.warning("Index creation warning: %s", exc)


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Return the connected database. Call connect_mongo() first (at startup)."""
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect_mongo() during startup.")
    return _db


async def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")
    _client = None
    _db = None


async def mongo_health() -> str:
    """Return 'ok' or 'error' for the health check."""
    try:
        if _client is None:
            return "error"
        await _client.admin.command("ping")
        return "ok"
    except Exception:  # pragma: no cover - network dependent
        return "error"
