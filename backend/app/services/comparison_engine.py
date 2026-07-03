"""Comparison engine: deterministic gap analysis (DDD Section 8). No LLM.

Operates on the structured output of LLM Call 1 (employee skills) and the role
requirements from MongoDB. Produces the comparison result, readiness score, and
per-category breakdown.
"""
from __future__ import annotations

from typing import Dict, List, Optional


def _find_in(items: List[Dict], name_lower: str) -> Optional[Dict]:
    for item in items:
        if item["skill_name"].lower() == name_lower:
            return item
    return None


def compare_skills(
    employee_skills: List[Dict], role_requirements: List[Dict]
) -> Dict:
    """Match employee skills against role requirements (DDD 8.2)."""
    emp_map = {s["skill_name"].lower(): s for s in employee_skills}
    matched: List[Dict] = []
    missing: List[Dict] = []
    fully_met: List[Dict] = []
    exceeded: List[Dict] = []

    for req in role_requirements:
        req_name = req["skill_name"]
        req_level = req["required_level"]
        cat = req["category"]
        emp = emp_map.get(req_name.lower())

        if emp is None:
            missing.append(
                {"skill_name": req_name, "required_level": req_level, "category": cat}
            )
            continue

        emp_level = emp["estimated_level"]
        gap = req_level - emp_level
        if gap > 0:
            matched.append(
                {
                    "skill_name": req_name,
                    "employee_level": emp_level,
                    "required_level": req_level,
                    "gap": gap,
                    "status": "below_required",
                    "category": cat,
                }
            )
        elif gap == 0:
            fully_met.append(
                {
                    "skill_name": req_name,
                    "employee_level": emp_level,
                    "required_level": req_level,
                    "gap": 0,
                    "category": cat,
                }
            )
        else:
            exceeded.append(
                {
                    "skill_name": req_name,
                    "employee_level": emp_level,
                    "required_level": req_level,
                    "surplus": abs(gap),
                    "category": cat,
                }
            )

    required_names = {r["skill_name"].lower() for r in role_requirements}
    additional = [
        s for s in employee_skills if s["skill_name"].lower() not in required_names
    ]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "fully_met_skills": fully_met,
        "exceeded_skills": exceeded,
        "additional_skills": additional,
    }


def calculate_readiness_score(
    comparison_result: Dict, role_requirements: List[Dict]
) -> float:
    """Readiness score in [0, 100] (DDD 8.3)."""
    total = len(role_requirements)
    if total == 0:
        return 100.0

    score_sum = 0.0
    for req in role_requirements:
        req_level = req["required_level"]
        name_lower = req["skill_name"].lower()

        fully = _find_in(comparison_result["fully_met_skills"], name_lower)
        exceeded = _find_in(comparison_result["exceeded_skills"], name_lower)
        matched = _find_in(comparison_result["matched_skills"], name_lower)

        if fully or exceeded:
            score_sum += 1.0
        elif matched:
            score_sum += matched["employee_level"] / req_level
        else:
            score_sum += 0.0

    return round((score_sum / total) * 100, 1)


def calculate_category_breakdown(
    comparison_result: Dict, role_requirements: List[Dict]
) -> Dict[str, Dict]:
    """Per-category readiness breakdown (DDD 8.4)."""
    categories: Dict[str, Dict] = {}
    for req in role_requirements:
        cat = req["category"]
        if cat not in categories:
            categories[cat] = {
                "total": 0,
                "met": 0,
                "gaps": 0,
                "missing": 0,
                "score_sum": 0.0,
            }
        categories[cat]["total"] += 1
        name_lower = req["skill_name"].lower()
        req_level = req["required_level"]

        if _find_in(comparison_result["fully_met_skills"], name_lower):
            categories[cat]["met"] += 1
            categories[cat]["score_sum"] += 1.0
        elif _find_in(comparison_result["exceeded_skills"], name_lower):
            categories[cat]["met"] += 1
            categories[cat]["score_sum"] += 1.0
        else:
            matched = _find_in(comparison_result["matched_skills"], name_lower)
            if matched:
                categories[cat]["gaps"] += 1
                categories[cat]["score_sum"] += matched["employee_level"] / req_level
            else:
                categories[cat]["missing"] += 1

    for _cat, data in categories.items():
        data["score"] = round((data["score_sum"] / data["total"]) * 100, 1)
        del data["score_sum"]
    return categories


def build_readiness_breakdown(
    comparison_result: Dict, role_requirements: List[Dict]
) -> Dict[str, int]:
    """Summary counts for the dashboard readiness card."""
    return {
        "total_required_skills": len(role_requirements),
        "fully_met": len(comparison_result["fully_met_skills"])
        + len(comparison_result["exceeded_skills"]),
        "partially_met": len(comparison_result["matched_skills"]),
        "missing": len(comparison_result["missing_skills"]),
    }
