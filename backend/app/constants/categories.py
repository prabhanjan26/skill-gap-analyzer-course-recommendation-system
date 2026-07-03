"""Predefined 12-category skill taxonomy.

This module is the SINGLE SOURCE OF TRUTH for skill categories across the whole
system: admin role forms, LLM extraction prompts, the course catalog, and the
dashboard category breakdown. See DDD Section 2.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List


class SkillCategory(str, Enum):
    # --- Original DDD taxonomy (12) ---
    PROGRAMMING_LANGUAGES = "programming_languages"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASES = "databases"
    DEVOPS = "devops"
    CLOUD = "cloud"
    ARCHITECTURE = "architecture"
    DATA_ENGINEERING = "data_engineering"
    DATA_SCIENCE = "data_science"
    QUALITY = "quality"
    SECURITY = "security"
    SOFT_SKILLS = "soft_skills"
    # --- Additional industry-standard categories ---
    MOBILE = "mobile"
    UI_UX = "ui_ux"
    AI_ML = "ai_ml"
    NETWORKING = "networking"
    BLOCKCHAIN = "blockchain"
    GAME_DEVELOPMENT = "game_development"
    EMBEDDED_IOT = "embedded_iot"
    PRODUCT_MANAGEMENT = "product_management"


CATEGORY_LABELS: Dict[SkillCategory, str] = {
    SkillCategory.PROGRAMMING_LANGUAGES: "Programming Languages",
    SkillCategory.FRONTEND: "Frontend Development",
    SkillCategory.BACKEND: "Backend Development",
    SkillCategory.DATABASES: "Databases",
    SkillCategory.DEVOPS: "DevOps & Infrastructure",
    SkillCategory.CLOUD: "Cloud Platforms",
    SkillCategory.ARCHITECTURE: "System Architecture",
    SkillCategory.DATA_ENGINEERING: "Data Engineering",
    SkillCategory.DATA_SCIENCE: "Data Science & ML",
    SkillCategory.QUALITY: "Quality & Testing",
    SkillCategory.SECURITY: "Security",
    SkillCategory.SOFT_SKILLS: "Soft Skills & Leadership",
    SkillCategory.MOBILE: "Mobile Development",
    SkillCategory.UI_UX: "UI/UX & Design",
    SkillCategory.AI_ML: "AI & Machine Learning",
    SkillCategory.NETWORKING: "Networking & Systems",
    SkillCategory.BLOCKCHAIN: "Blockchain & Web3",
    SkillCategory.GAME_DEVELOPMENT: "Game Development",
    SkillCategory.EMBEDDED_IOT: "Embedded & IoT",
    SkillCategory.PRODUCT_MANAGEMENT: "Product & Project Management",
}

# Short codes used in course_id: COURSE-{CATEGORY_CODE}-{LEVEL_CODE}-{SEQ}
CATEGORY_CODES: Dict[SkillCategory, str] = {
    SkillCategory.PROGRAMMING_LANGUAGES: "PL",
    SkillCategory.FRONTEND: "FE",
    SkillCategory.BACKEND: "BE",
    SkillCategory.DATABASES: "DB",
    SkillCategory.DEVOPS: "DO",
    SkillCategory.CLOUD: "CL",
    SkillCategory.ARCHITECTURE: "ARCH",
    SkillCategory.DATA_ENGINEERING: "DE",
    SkillCategory.DATA_SCIENCE: "DS",
    SkillCategory.QUALITY: "QA",
    SkillCategory.SECURITY: "SEC",
    SkillCategory.SOFT_SKILLS: "SOFT",
    SkillCategory.MOBILE: "MOB",
    SkillCategory.UI_UX: "UX",
    SkillCategory.AI_ML: "AIML",
    SkillCategory.NETWORKING: "NET",
    SkillCategory.BLOCKCHAIN: "BC",
    SkillCategory.GAME_DEVELOPMENT: "GAME",
    SkillCategory.EMBEDDED_IOT: "IOT",
    SkillCategory.PRODUCT_MANAGEMENT: "PROD",
}

VALID_CATEGORIES: List[str] = [c.value for c in SkillCategory]

# Custom categories entered by admins must be lowercase slug-like tokens.
import re as _re

_CUSTOM_CATEGORY_PATTERN = _re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
MAX_CUSTOM_CATEGORY_LEN = 50


def category_choices() -> List[Dict[str, str]]:
    """Return category choices as [{key, label}, ...] for API / dropdowns."""
    return [{"key": c.value, "label": CATEGORY_LABELS[c]} for c in SkillCategory]


def is_valid_category(value: str) -> bool:
    return value in VALID_CATEGORIES


def is_valid_custom_category(value: str) -> bool:
    """A custom category is an unknown but well-formed slug (<= 50 chars)."""
    return (
        bool(value)
        and len(value) <= MAX_CUSTOM_CATEGORY_LEN
        and bool(_CUSTOM_CATEGORY_PATTERN.match(value))
    )


def normalize_category(value: str) -> str:
    """Accept a predefined category or a well-formed custom slug.

    Raises ValueError otherwise. Custom values are returned as-is (already
    validated as a slug); predefined values are returned unchanged.
    """
    if value in VALID_CATEGORIES:
        return value
    if is_valid_custom_category(value):
        return value
    raise ValueError(f"Invalid category: {value}")
