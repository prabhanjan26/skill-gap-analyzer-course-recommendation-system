"""Two-stage course recommendation pipeline (DDD Section 9).

Stage 1: semantic retrieval from ChromaDB per skill gap (top_k=15, deduped,
         capped at 60 unique courses).
Stage 2: LLM re-ranking into a personalized learning path (llm_service call 2).
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional, Tuple

from app.models.enums import LEVEL_LABELS
from app.services import llm_service
from app.services.vectorstore_service import search_courses

logger = logging.getLogger(__name__)

TOP_K_PER_SKILL = 15
MAX_CANDIDATES_TO_STAGE2 = 60


def build_course_query(
    skill_name: str, gap_from: Optional[int], gap_to: int, category: Optional[str]
) -> Tuple[str, Dict]:
    """Construct the semantic query text + metadata filter (DDD 9.1.1)."""
    if gap_from is None:
        query = f"{skill_name} fundamentals introduction beginner"
        level_filter: Dict = {"level_numeric": {"$lte": 2}}
    elif gap_to - gap_from == 1:
        query = f"{skill_name} {LEVEL_LABELS[gap_to]} deep dive"
        level_filter = {"level_numeric": {"$gte": gap_from, "$lte": gap_to}}
    else:
        query = (
            f"{skill_name} comprehensive {LEVEL_LABELS[gap_from]} to {LEVEL_LABELS[gap_to]}"
        )
        level_filter = {"level_numeric": {"$gte": gap_from}}

    if category:
        level_filter["primary_category"] = category

    return query, level_filter


def _collect_gaps(comparison_result: Dict) -> List[Dict]:
    """Combine missing + below_required matched skills into gap descriptors."""
    gaps: List[Dict] = []
    for skill in comparison_result.get("missing_skills", []):
        gaps.append(
            {
                "skill_name": skill["skill_name"],
                "gap_from": None,
                "gap_to": skill["required_level"],
                "category": skill.get("category"),
                "gap_type": "missing",
            }
        )
    for skill in comparison_result.get("matched_skills", []):
        gaps.append(
            {
                "skill_name": skill["skill_name"],
                "gap_from": skill["employee_level"],
                "gap_to": skill["required_level"],
                "category": skill.get("category"),
                "gap_type": "below_required",
            }
        )
    return gaps


def retrieve_candidates(comparison_result: Dict) -> Tuple[List[Dict], List[Dict]]:
    """Stage 1: retrieve deduplicated candidate courses across all gaps.

    Returns (candidate_courses, gaps). Candidates capped at 60 unique course_ids.
    """
    gaps = _collect_gaps(comparison_result)
    seen_ids = set()
    candidates: List[Dict] = []

    for gap in gaps:
        query, where = build_course_query(
            gap["skill_name"], gap["gap_from"], gap["gap_to"], gap["category"]
        )
        results = search_courses(query, where, top_k=TOP_K_PER_SKILL)
        for course in results:
            cid = course.get("course_id")
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)
            candidates.append(course)
            if len(candidates) >= MAX_CANDIDATES_TO_STAGE2:
                logger.info("Reached candidate cap (%d)", MAX_CANDIDATES_TO_STAGE2)
                return candidates, gaps

    return candidates, gaps


def assemble_reranking_context(
    comparison_result: Dict, candidate_courses: List[Dict]
) -> Tuple[str, str]:
    """Build (gaps_json, candidate_courses_json) for the LLM (DDD 9.2.1)."""
    gaps = []
    for skill in comparison_result.get("missing_skills", []):
        gaps.append(
            {
                "skill_name": skill["skill_name"],
                "current_level": None,
                "target_level": skill["required_level"],
                "gap_type": "missing",
            }
        )
    for skill in comparison_result.get("matched_skills", []):
        gaps.append(
            {
                "skill_name": skill["skill_name"],
                "current_level": skill["employee_level"],
                "target_level": skill["required_level"],
                "gap_type": "below_required",
            }
        )

    courses_compact = [
        {
            "course_id": c.get("course_id"),
            "title": c.get("title"),
            "provider": c.get("provider"),
            "level": c.get("level"),
            "rating": c.get("rating"),
            "description": (c.get("description") or "")[:200],
        }
        for c in candidate_courses
    ]

    return json.dumps(gaps), json.dumps(courses_compact)


def generate_recommendations(
    comparison_result: Dict, employee_name: str, role_name: str
) -> Dict:
    """Full recommendation pipeline (Stage 1 + Stage 2).

    Returns {
      recommendations, stage1_count, after_rerank_count, notices, llm_called
    }.
    """
    notices: List[str] = []
    candidates, gaps = retrieve_candidates(comparison_result)

    if not gaps:
        return {
            "recommendations": [],
            "stage1_count": 0,
            "after_rerank_count": 0,
            "notices": ["No skill gaps detected - no course recommendations needed."],
            "llm_called": False,
        }

    if not candidates:
        return {
            "recommendations": [],
            "stage1_count": 0,
            "after_rerank_count": 0,
            "notices": ["No matching courses found for the detected skill gaps."],
            "llm_called": False,
        }

    gaps_json, courses_json = assemble_reranking_context(comparison_result, candidates)

    # Stage 2: LLM re-ranking (this is the SECOND and final LLM call).
    ranked = llm_service.rerank_courses(
        gaps_json=gaps_json,
        candidate_courses_json=courses_json,
        employee_name=employee_name,
        role_name=role_name,
    )

    recommendations = _enrich_recommendations(ranked, candidates, gaps)
    after_count = sum(len(r["courses"]) for r in recommendations)

    if not recommendations:
        notices.append("Re-ranking produced no recommendations.")

    return {
        "recommendations": recommendations,
        "stage1_count": len(candidates),
        "after_rerank_count": after_count,
        "notices": notices,
        "llm_called": True,
    }


def _enrich_recommendations(
    ranked: List[Dict], candidates: List[Dict], gaps: List[Dict]
) -> List[Dict]:
    """Attach gap_from/gap_to and fill missing course fields from candidates."""
    course_by_id = {c["course_id"]: c for c in candidates}
    gap_by_skill = {g["skill_name"].lower(): g for g in gaps}

    out: List[Dict] = []
    for group in ranked:
        skill_name = str(group.get("skill_name", "")).strip()
        if not skill_name:
            continue
        gap = gap_by_skill.get(skill_name.lower(), {})
        courses_out: List[Dict] = []
        for course in group.get("courses", []):
            if not isinstance(course, dict):
                continue
            cid = course.get("course_id")
            source = course_by_id.get(cid, {})
            courses_out.append(
                {
                    "course_id": cid,
                    "title": course.get("title") or source.get("title", ""),
                    "provider": course.get("provider") or source.get("provider", ""),
                    "level": course.get("level") or source.get("level", ""),
                    "duration_hours": source.get("duration_hours"),
                    "relevance_score": _safe_float(course.get("relevance_score")),
                    "reasoning": course.get("reasoning", ""),
                }
            )
        out.append(
            {
                "skill_name": skill_name,
                "gap_from": gap.get("gap_from"),
                "gap_to": gap.get("gap_to"),
                "courses": courses_out,
            }
        )
    return out


def _safe_float(value) -> Optional[float]:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None
