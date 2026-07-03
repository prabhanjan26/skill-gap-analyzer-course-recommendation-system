"""Course embedding pipeline: MongoDB -> embed -> ChromaDB (DDD Section 10).

MongoDB is the source of truth. This pipeline reads unembedded courses,
constructs the embedding text ON-THE-FLY (never stored in MongoDB), embeds them
via the SAME embedding_service singleton used for resumes, upserts vectors into
ChromaDB, and flips is_embedded=true. Supports incremental and full rebuild.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from app.db.chromadb_client import get_course_collection
from app.db.mongodb import COURSE_CATALOG, get_mongo_db
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

BATCH_SIZE = 256


def _build_embedding_text(course: Dict) -> str:
    """title + skill_tags + description[:200] + level (DDD 4.3.1)."""
    return " ".join(
        [
            course.get("title", ""),
            " ".join(course.get("skill_tags", [])),
            (course.get("description", "") or "")[:200],
            course.get("level", ""),
        ]
    ).strip()


def _build_metadata(course: Dict) -> Dict:
    """ChromaDB metadata must be scalar; skill_tags becomes a comma string."""
    return {
        "course_id": course["course_id"],
        "title": course.get("title", ""),
        "provider": course.get("provider", ""),
        "level": course.get("level", ""),
        "level_numeric": course.get("level_numeric", 0),
        "primary_category": course.get("primary_category", ""),
        "skill_tags": ",".join(course.get("skill_tags", [])),
        "duration_hours": course.get("duration_hours", 0),
        "rating": course.get("rating", 0.0),
    }


async def run_course_embedding_pipeline(full_rebuild: bool = False) -> int:
    """Embed courses into ChromaDB. Returns the number of courses processed."""
    db = get_mongo_db()
    collection = db[COURSE_CATALOG]
    embedding_svc = get_embedding_service()  # SAME singleton as resume pipeline
    chroma_col = get_course_collection()

    query = {} if full_rebuild else {"is_embedded": False}
    courses: List[Dict] = await collection.find(query).to_list(length=None)
    if not courses:
        logger.info("Course embedding pipeline: nothing to embed.")
        return 0

    if full_rebuild and chroma_col.count() > 0:
        existing = chroma_col.get()["ids"]
        if existing:
            chroma_col.delete(ids=existing)
        logger.info("Full rebuild: cleared %d existing course vectors", len(existing))

    logger.info("Embedding %d courses (full_rebuild=%s)", len(courses), full_rebuild)

    # Construct embedding text on-the-fly (not stored in MongoDB).
    texts = [_build_embedding_text(c) for c in courses]

    # Generate embeddings via the shared embedding_service, in batches.
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        embs = embedding_svc.encode(batch)
        all_embeddings.extend(embs.tolist())

    # Upsert into ChromaDB in batches.
    for i in range(0, len(courses), BATCH_SIZE):
        batch = courses[i : i + BATCH_SIZE]
        chroma_col.upsert(
            ids=[c["course_id"] for c in batch],
            documents=texts[i : i + BATCH_SIZE],
            embeddings=all_embeddings[i : i + BATCH_SIZE],
            metadatas=[_build_metadata(c) for c in batch],
        )
        logger.info("Upserted courses %d-%d into ChromaDB", i, i + len(batch))

    # Mark as embedded in MongoDB (resume-safe: only touch processed ids).
    ids = [c["_id"] for c in courses]
    await collection.update_many({"_id": {"$in": ids}}, {"$set": {"is_embedded": True}})

    logger.info("Course embedding pipeline complete: %d courses embedded", len(courses))
    return len(courses)


async def auto_embed_on_startup() -> None:
    """Startup integration (DDD 10.3): self-heal / incremental embed."""
    db = get_mongo_db()
    collection = db[COURSE_CATALOG]
    chroma_col = get_course_collection()

    chroma_count = chroma_col.count()
    mongo_count = await collection.count_documents({})
    unembedded = await collection.count_documents({"is_embedded": False})

    if mongo_count == 0:
        logger.warning(
            "course_catalog is empty. Run scripts/generate_courses.py to seed courses."
        )
        return

    if chroma_count == 0 and mongo_count > 0:
        logger.info("ChromaDB empty - running full embedding pipeline...")
        await run_course_embedding_pipeline(full_rebuild=True)
    elif unembedded > 0:
        logger.info("%d new courses - running incremental embedding...", unembedded)
        await run_course_embedding_pipeline(full_rebuild=False)
    else:
        logger.info(
            "Course index up to date (mongo=%d, chroma=%d)", mongo_count, chroma_count
        )
