"""Analysis orchestrator: coordinates the full 7-stage pipeline (DDD 6, 11.3).

Sequence:
  1. Resume parsing            (resume_parser)
  2. Text chunking             (chunking_service)
  3. Embedding generation      (embedding_service)
  4. Vector store indexing     (vectorstore_service.store_resume_chunks)
  5. Semantic search           (vectorstore_service.search_resume_chunks)
  6. RAG context assembly      (rag_service)
  7. LLM skill extraction      (llm_service.extract_skills)  <-- LLM call 1
Then deterministic comparison (comparison_engine) and the two-stage course
recommendation pipeline (recommendation_service, whose Stage 2 is LLM call 2).

Exactly two LLM calls per analysis (the 2nd is skipped only when there are no
gaps / no candidate courses, which cannot exceed the budget).
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from app.db.chromadb_client import courses_indexed_count
from app.services import (
    comparison_engine,
    llm_service,
    rag_service,
    recommendation_service,
    vectorstore_service,
)
from app.services.chunking_service import chunk_text
from app.services.embedding_service import get_embedding_service
from app.services.resume_parser import parse_resume

logger = logging.getLogger(__name__)

TOP_K_RESUME = 5
MAX_CHUNKS = 20  # DDD 12.5: truncate very long resumes


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_analysis(
    file_path: str, mime_type: str, role_doc: Dict, employee_name: str = ""
) -> Dict:
    """Execute the full analysis pipeline. Returns the AnalysisResponse dict.

    File validation / IO errors from parse_resume propagate to the route.
    """
    start = time.perf_counter()
    session_id = f"sess_{uuid.uuid4().hex[:10]}"
    notices: List[str] = []
    llm_calls = 0

    role_name = role_doc["role_name"]
    role_slug = role_doc["role_slug"]
    role_skills = role_doc["skills"]

    # --- Stage 1: Parse ---
    parsed = parse_resume(file_path, mime_type)
    raw_text = parsed["raw_text"]

    # --- Stage 2: Chunk ---
    chunks = chunk_text(raw_text)
    chunks_generated = len(chunks)
    if chunks_generated > MAX_CHUNKS:
        chunks = chunks[:MAX_CHUNKS]
        notices.append(
            f"Resume truncated to first {MAX_CHUNKS} chunks (of {chunks_generated})."
        )
        logger.warning("Very long resume: truncated to %d chunks", MAX_CHUNKS)

    # --- Stage 3: Embed ---
    embedding_svc = get_embedding_service()
    chunk_texts = [c["text"] for c in chunks]
    embeddings = embedding_svc.encode(chunk_texts).tolist() if chunk_texts else []

    # --- Stage 4: Index ---
    vectorstore_service.store_resume_chunks(
        session_id, chunks, embeddings, employee_name=employee_name
    )

    # --- Stage 5: Semantic search ---
    query_text = " ".join(s["skill_name"] for s in role_skills)
    retrieved = vectorstore_service.search_resume_chunks(
        query_text, session_id, top_k=TOP_K_RESUME
    )
    chunks_retrieved = len(retrieved)

    # --- Stage 6: RAG context ---
    context = rag_service.build_skill_extraction_context(retrieved, role_skills)

    # --- Stage 7: LLM extraction (call 1) ---
    extracted_skills = llm_service.extract_skills(
        resume_context=context["context_text"],
        role_name=role_name,
        role_skills_json=context["role_requirements"],
    )
    llm_calls += 1

    if not extracted_skills:
        notices.append(
            "No identifiable skills could be extracted from the resume."
        )

    # --- Comparison (deterministic) ---
    comparison = comparison_engine.compare_skills(extracted_skills, role_skills)
    readiness_score = comparison_engine.calculate_readiness_score(comparison, role_skills)
    category_breakdown = comparison_engine.calculate_category_breakdown(
        comparison, role_skills
    )
    readiness_breakdown = comparison_engine.build_readiness_breakdown(
        comparison, role_skills
    )
    comparison["category_breakdown"] = category_breakdown

    # --- Course recommendations (Stage 1 retrieval + Stage 2 LLM call 2) ---
    rec = recommendation_service.generate_recommendations(
        comparison, employee_name=employee_name, role_name=role_name
    )
    if rec["llm_called"]:
        llm_calls += 1
    notices.extend(rec["notices"])

    # --- Cleanup transient resume chunks for this session ---
    try:
        vectorstore_service.clear_session_chunks(session_id)
    except Exception:  # pragma: no cover
        pass

    duration_ms = int((time.perf_counter() - start) * 1000)

    return {
        "session_id": session_id,
        "employee_name": employee_name or None,
        "role_analyzed": {"role_name": role_name, "role_slug": role_slug},
        "extracted_skills": extracted_skills,
        "comparison_result": comparison,
        "readiness_score": readiness_score,
        "readiness_breakdown": readiness_breakdown,
        "course_recommendations": rec["recommendations"],
        "analysis_metadata": {
            "pipeline_duration_ms": duration_ms,
            "llm_calls": llm_calls,
            "chunks_generated": chunks_generated,
            "chunks_retrieved": chunks_retrieved,
            "courses_in_catalog": courses_indexed_count(),
            "courses_retrieved_stage1": rec["stage1_count"],
            "courses_after_reranking": rec["after_rerank_count"],
            "timestamp": _now_iso(),
        },
        "notices": notices,
    }
