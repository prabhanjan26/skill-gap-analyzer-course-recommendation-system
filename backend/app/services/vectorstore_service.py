"""Stages 4 & 5: ChromaDB vector store operations (DDD 6).

- store_resume_chunks(): upsert resume chunk embeddings (scoped by session_id).
- search_resume_chunks(): semantic search over a session's chunks.
- search_courses(): semantic search over the course_embeddings collection.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.db.chromadb_client import get_course_collection, get_resume_collection
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


def _resume_chunk_id(session_id: str, index: int) -> str:
    return f"resume_{session_id}_chunk_{index:03d}"


def clear_session_chunks(session_id: str) -> None:
    """Delete any existing chunks for a session before re-upserting."""
    collection = get_resume_collection()
    try:
        collection.delete(where={"session_id": session_id})
    except Exception as exc:  # pragma: no cover
        logger.warning("Could not clear prior chunks for %s: %s", session_id, exc)


def store_resume_chunks(
    session_id: str,
    chunks: List[Dict],
    embeddings: List[List[float]],
    employee_name: Optional[str] = None,
) -> int:
    """Upsert resume chunks into the resume_chunks collection.

    `chunks` items are { text, index, section }. Returns count stored.
    """
    if not chunks:
        return 0

    collection = get_resume_collection()
    clear_session_chunks(session_id)

    total = len(chunks)
    ids, documents, metadatas = [], [], []
    for chunk in chunks:
        idx = chunk["index"]
        ids.append(_resume_chunk_id(session_id, idx))
        documents.append(chunk["text"])
        metadatas.append(
            {
                "session_id": session_id,
                "employee_name": employee_name or "",
                "chunk_index": idx,
                "source_section": chunk.get("section", "other"),
                "total_chunks": total,
            }
        )

    collection.upsert(
        ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings
    )
    logger.info("Stored %d resume chunks for session %s", total, session_id)
    return total


def search_resume_chunks(
    query_text: str, session_id: str, top_k: int = 5
) -> List[Dict]:
    """Return the top_k most relevant chunks for a session.

    Result items: { text, metadata, distance }.
    """
    collection = get_resume_collection()
    embedding = get_embedding_service().encode_one(query_text)

    result = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where={"session_id": session_id},
        include=["documents", "metadatas", "distances"],
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    out: List[Dict] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        out.append({"text": doc, "metadata": meta, "distance": dist})
    return out


def search_courses(
    query_text: str, where: Optional[Dict], top_k: int = 15
) -> List[Dict]:
    """Semantic search over course_embeddings with optional metadata filter.

    Returns course dicts assembled from ChromaDB metadata + document snippet.
    """
    collection = get_course_collection()
    embedding = get_embedding_service().encode_one(query_text)

    query_kwargs = {
        "query_embeddings": [embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    normalized_where = _normalize_where(where)
    if normalized_where:
        query_kwargs["where"] = normalized_where

    try:
        result = collection.query(**query_kwargs)
    except Exception as exc:  # pragma: no cover - self-heal on filter issues
        logger.warning("Course query failed (%s); retrying without filter", exc)
        query_kwargs.pop("where", None)
        result = collection.query(**query_kwargs)

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    courses: List[Dict] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        meta = meta or {}
        skill_tags = meta.get("skill_tags", "")
        courses.append(
            {
                "course_id": meta.get("course_id"),
                "title": meta.get("title", ""),
                "provider": meta.get("provider", ""),
                "level": meta.get("level", ""),
                "level_numeric": meta.get("level_numeric"),
                "primary_category": meta.get("primary_category", ""),
                "skill_tags": skill_tags.split(",") if skill_tags else [],
                "duration_hours": meta.get("duration_hours"),
                "rating": meta.get("rating"),
                "description": doc or "",
                "distance": dist,
                "similarity": (1.0 - dist) if dist is not None else None,
            }
        )
    return courses


def _normalize_where(where: Optional[Dict]) -> Optional[Dict]:
    """Normalize a filter into ChromaDB-compatible form.

    - Multiple fields are combined under a single top-level $and.
    - A field with multiple comparison operators (e.g. {'$gte': 2, '$lte': 3})
      is split into one clause per operator, since Chroma expects a single
      operator per field expression.
    """
    if not where:
        return None
    clauses = []
    for key, value in where.items():
        if isinstance(value, dict) and len(value) > 1:
            for op, op_val in value.items():
                clauses.append({key: {op: op_val}})
        else:
            clauses.append({key: value})
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}
