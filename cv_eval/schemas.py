from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


# -----------------------
# Common / Base
# -----------------------

class Band(str, Enum):
    Excellent = "Excellent"
    Strong = "Strong"
    Partial = "Partial"
    Weak = "Weak"


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


# -----------------------
# Scoring payloads/results
# -----------------------

class SubScore(BaseSchema):
    dimension: str = Field(..., description="Scoring dimension name", examples=["ats_structure"])
    score: float = Field(..., ge=0, le=100, description="Score for this dimension", examples=[7.5])
    evidence: List[str] = Field(
        default_factory=list,
        description="Evidence spans from CV text (top 3 recommended)",
        examples=[["Reduced API response time by 40%"]],
    )
    max_score: float = Field(..., gt=0, description="Maximum possible score for this dimension", examples=[10.0])


class ScoreResult(BaseSchema):
    overall_score: float = Field(..., ge=0, le=100, description="Overall score out of 100", examples=[78.25])
    band: Optional[Band] = Field(None, description="Score band")
    subscores: List[SubScore] = Field(default_factory=list, description="Detailed subscores with evidence")

    @field_validator("subscores")
    @classmethod
    def non_empty_subscores(cls, v: List[SubScore]) -> List[SubScore]:
        return v


class ConstraintsDisclosure(BaseSchema):
    location_match: Optional[bool] = Field(None, description="Location requirements met")
    work_authorization: Optional[bool] = Field(None, description="Work authorization requirements met")
    remote_work: Optional[bool] = Field(None, description="Remote work preferences aligned")
    travel_requirements: Optional[bool] = Field(None, description="Travel requirements acceptable")

    constraints_score: float = Field(..., ge=0, le=10, description="Constraints score (0-10)", examples=[10.0])
    constraints_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence for constraints assessment",
        examples=[["Remote option noted in JD"]],
    )


# -----------------------
# Key takeaways (new addition)
# -----------------------

class KeyTakeaways(BaseSchema):
    red_flags: List[str] = Field(default_factory=list, description="Critical deal-breakers")
    green_flags: List[str] = Field(default_factory=list, description="Standout strengths")


# -----------------------
# Evaluation results
# -----------------------

class CVEvaluationResult(BaseSchema):
    cv_quality: ScoreResult = Field(..., description="CV quality assessment")
    jd_match: ScoreResult = Field(..., description="Job description match assessment")

    fit_index: float = Field(..., ge=0, le=100, description="Overall fit index (0-100)", examples=[81.6])
    band: Band = Field(..., description="Overall fit band", examples=[Band.Strong])

    constraints_disclosure: Optional[ConstraintsDisclosure] = Field(None, description="Constraints assessment")
    key_takeaways: Optional[KeyTakeaways] = Field(None, description="Highlights: red flags and green flags")

    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC evaluation timestamp")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CVEvaluationRequest(BaseSchema):
    cv_text: str = Field(..., description="CV text content")
    jd_text: str = Field(..., description="Job description text content")
    include_constraints: bool = Field(
        True,
        description="Whether to include constraints in fit calculation (if False, exclude constraints from total)",
    )


# -----------------------
# Alias for compatibility
# -----------------------

# Use EvaluationResult everywhere in new LLM scorer
EvaluationResult = CVEvaluationResult
