"""Pydantic request/response models. See DDD Sections 3, 5, and 8."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants.categories import VALID_CATEGORIES, SkillCategory, normalize_category


# ---------------------------------------------------------------------------
# Response envelope (DDD 5.1)
# ---------------------------------------------------------------------------
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Role / competency_matrix (DDD 3.1)
# ---------------------------------------------------------------------------
class SkillRequirement(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=80)
    required_level: int = Field(..., ge=1, le=4)
    category: str

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        # Accept a predefined category OR a well-formed custom slug.
        return normalize_category(v)

    @field_validator("skill_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("skill_name cannot be empty")
        return v


class RoleCreate(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=500)
    skills: List[SkillRequirement] = Field(..., min_length=1)

    @field_validator("role_name")
    @classmethod
    def _strip_role_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("role_name cannot be empty")
        return v


class RoleUpdate(BaseModel):
    """Update allows partial updates; omitted fields are left unchanged."""

    role_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    skills: Optional[List[SkillRequirement]] = Field(default=None, min_length=1)

    @field_validator("role_name")
    @classmethod
    def _strip_role_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("role_name cannot be empty")
        return v


class RoleSummary(BaseModel):
    """Compact role representation for list views (DDD 5.4)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    role_name: str
    role_slug: str
    skills_count: int
    categories: List[str] = Field(default_factory=list)
    updated_at: Optional[str] = None


class EmployeeRoleSummary(BaseModel):
    role_name: str
    role_slug: str
    skills_count: int


# ---------------------------------------------------------------------------
# Analysis response models (DDD 5.10)
# ---------------------------------------------------------------------------
class ExtractedSkill(BaseModel):
    skill_name: str
    estimated_level: int = Field(..., ge=1, le=4)
    confidence: float = Field(..., ge=0.0, le=1.0)
    category: str
    evidence_snippet: Optional[str] = ""


class MatchedSkill(BaseModel):
    skill_name: str
    employee_level: int
    required_level: int
    gap: int
    status: str
    category: str


class MissingSkill(BaseModel):
    skill_name: str
    required_level: int
    category: str


class FullyMetSkill(BaseModel):
    skill_name: str
    employee_level: int
    required_level: int
    gap: int
    category: str


class ExceededSkill(BaseModel):
    skill_name: str
    employee_level: int
    required_level: int
    surplus: int
    category: str


class CategoryScore(BaseModel):
    total: int
    met: int
    gaps: int
    missing: int
    score: float


class ComparisonResult(BaseModel):
    matched_skills: List[MatchedSkill] = Field(default_factory=list)
    missing_skills: List[MissingSkill] = Field(default_factory=list)
    fully_met_skills: List[FullyMetSkill] = Field(default_factory=list)
    exceeded_skills: List[ExceededSkill] = Field(default_factory=list)
    additional_skills: List[ExtractedSkill] = Field(default_factory=list)
    category_breakdown: Dict[str, CategoryScore] = Field(default_factory=dict)


class ReadinessBreakdown(BaseModel):
    total_required_skills: int
    fully_met: int
    partially_met: int
    missing: int


class RecommendedCourse(BaseModel):
    course_id: str
    title: str
    provider: str
    level: str
    duration_hours: Optional[float] = None
    relevance_score: Optional[float] = None
    reasoning: Optional[str] = ""


class SkillRecommendation(BaseModel):
    skill_name: str
    gap_from: Optional[int] = None
    gap_to: Optional[int] = None
    courses: List[RecommendedCourse] = Field(default_factory=list)


class AnalysisMetadata(BaseModel):
    pipeline_duration_ms: int
    llm_calls: int
    chunks_generated: int
    chunks_retrieved: int
    courses_in_catalog: int
    courses_retrieved_stage1: int
    courses_after_reranking: int
    timestamp: str


class RoleAnalyzed(BaseModel):
    role_name: str
    role_slug: str


class AnalysisResponse(BaseModel):
    session_id: str
    employee_name: Optional[str] = None
    role_analyzed: RoleAnalyzed
    extracted_skills: List[ExtractedSkill] = Field(default_factory=list)
    comparison_result: ComparisonResult
    readiness_score: float
    readiness_breakdown: ReadinessBreakdown
    course_recommendations: List[SkillRecommendation] = Field(default_factory=list)
    analysis_metadata: AnalysisMetadata
    notices: List[str] = Field(default_factory=list)
