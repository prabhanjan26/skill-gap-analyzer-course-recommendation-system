"""Embedding runner (DDD Section 10.2 / 11.4): MongoDB -> embed -> ChromaDB.

Reads unembedded courses from MongoDB, embeds them via the shared
embedding_service, and upserts vectors into ChromaDB. Supports incremental
embedding (default) and a full rebuild.

Run:  python scripts/embed_courses.py [--full-rebuild]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.chromadb_client import get_course_collection  # noqa: E402
from app.db.mongodb import COURSE_CATALOG, close_mongo, connect_mongo, get_mongo_db  # noqa: E402
from app.services.course_embedding_pipeline import run_course_embedding_pipeline  # noqa: E402


async def _run(full_rebuild: bool) -> None:
    await connect_mongo()
    db = get_mongo_db()

    mongo_count = await db[COURSE_CATALOG].count_documents({})
    if mongo_count == 0:
        print("No courses in MongoDB. Run scripts/generate_courses.py first.")
        await close_mongo()
        return

    print(f"MongoDB course_catalog: {mongo_count} courses.")
    print(f"Running embedding pipeline (full_rebuild={full_rebuild})...")
    processed = await run_course_embedding_pipeline(full_rebuild=full_rebuild)

    chroma_count = get_course_collection().count()
    print(f"Embedded {processed} courses. ChromaDB course_embeddings count: {chroma_count}.")

    if chroma_count == mongo_count:
        print("Verification OK: ChromaDB count matches MongoDB course count.")
    else:
        print(f"WARNING: ChromaDB ({chroma_count}) != MongoDB ({mongo_count}).")

    await close_mongo()


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed courses from MongoDB into ChromaDB")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Clear ChromaDB and re-embed every course (default: incremental).",
    )
    args = parser.parse_args()
    asyncio.run(_run(full_rebuild=args.full_rebuild))


if __name__ == "__main__":
    main()
