"""ChromaDB persistent client singleton. See DDD Section 4 and 12.3.

Self-healing: the persistence directory is auto-created and collections are
created on demand via get_or_create_collection().
"""
from __future__ import annotations

import logging
import os

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)

RESUME_CHUNKS_COLLECTION = "resume_chunks"
COURSE_EMBEDDINGS_COLLECTION = "course_embeddings"
COSINE_METADATA = {"hnsw:space": "cosine"}

_client: "chromadb.ClientAPI | None" = None


def get_chroma_client() -> "chromadb.ClientAPI":
    """Return the persistent ChromaDB client, creating it (and its dir) if needed."""
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    persist_dir = os.path.abspath(settings.chroma_persist_dir)
    if not os.path.isdir(persist_dir):
        os.makedirs(persist_dir, exist_ok=True)
        logger.warning("Chroma persist dir missing — created %s", persist_dir)

    _client = chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
    )
    logger.info("ChromaDB PersistentClient initialized at %s", persist_dir)
    return _client


def get_course_collection():
    """Get-or-create the course_embeddings collection (cosine space)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COURSE_EMBEDDINGS_COLLECTION, metadata=COSINE_METADATA
    )


def get_resume_collection():
    """Get-or-create the resume_chunks collection (cosine space)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=RESUME_CHUNKS_COLLECTION, metadata=COSINE_METADATA
    )


def chroma_health() -> str:
    try:
        client = get_chroma_client()
        client.heartbeat()
        return "ok"
    except Exception:  # pragma: no cover
        return "error"


def courses_indexed_count() -> int:
    try:
        return get_course_collection().count()
    except Exception:  # pragma: no cover
        return 0
