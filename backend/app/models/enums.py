"""Shared enums: ProficiencyLevel and CourseLevel.

SkillCategory lives in `app.constants.categories` (the taxonomy source of truth)
and is re-exported here for convenience.
"""
from __future__ import annotations

from enum import Enum, IntEnum

from app.constants.categories import SkillCategory  # re-export

__all__ = ["ProficiencyLevel", "CourseLevel", "SkillCategory", "LEVEL_LABELS", "LEVEL_NUMERIC"]


class ProficiencyLevel(IntEnum):
    """Proficiency levels L1-L4 used for both required and estimated levels."""

    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


class CourseLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


# Numeric -> difficulty label (used for course query construction)
LEVEL_LABELS = {
    1: CourseLevel.BEGINNER.value,
    2: CourseLevel.INTERMEDIATE.value,
    3: CourseLevel.ADVANCED.value,
    4: CourseLevel.EXPERT.value,
}

# Difficulty label -> numeric
LEVEL_NUMERIC = {v: k for k, v in LEVEL_LABELS.items()}
