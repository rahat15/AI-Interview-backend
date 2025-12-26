from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# User schemas
class UserBase(BaseSchema):
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseSchema):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# Authentication schemas
class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    email: Optional[str] = None


class LoginRequest(BaseSchema):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


# Session schemas
class SessionBase(BaseSchema):
    role: str = Field(..., description="Job role being interviewed for")
    industry: str = Field(..., description="Industry sector")
    company: str = Field(..., description="Company name")


class SessionCreate(SessionBase):
    cv_file_id: Optional[str] = Field(None, description="CV artifact ID")
    jd_file_id: Optional[str] = Field(None, description="Job description artifact ID")
    jd_text: Optional[str] = Field(None, description="Job description text (alternative to file)")


class SessionUpdate(BaseSchema):
    status: Optional[str] = None
    plan_json: Optional[Dict[str, Any]] = None
    current_question_index: Optional[int] = None
    total_questions: Optional[int] = None


class Session(SessionBase):
    id: str
    user_id: str
    status: str
    plan_json: Optional[Dict[str, Any]] = None
    cv_file_id: Optional[str] = None
    jd_file_id: Optional[str] = None
    current_question_index: int
    total_questions: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Question schemas
class QuestionBase(BaseSchema):
    competency: str = Field(..., description="Competency area")
    difficulty: str = Field(..., description="Question difficulty level")
    text: str = Field(..., description="Question text")
    order_index: int = Field(..., description="Question order in session")


class QuestionCreate(QuestionBase):
    session_id: str
    meta: Optional[Dict[str, Any]] = None
    is_follow_up: bool = False
    parent_question_id: Optional[str] = None


class Question(QuestionBase):
    id: str
    session_id: str
    meta: Optional[Dict[str, Any]] = None
    is_follow_up: bool
    parent_question_id: Optional[str] = None
    created_at: datetime


class NextQuestionResponse(BaseSchema):
    question_id: str
    text: str
    competency: str
    difficulty: str
    meta: Optional[Dict[str, Any]] = None


# Answer schemas
class AnswerBase(BaseSchema):
    text: Optional[str] = Field(None, description="Answer text")
    audio_url: Optional[str] = Field(None, description="Audio file URL")


class AnswerCreate(AnswerBase):
    question_id: str
    session_id: str


class Answer(AnswerBase):
    id: str
    session_id: str
    question_id: str
    asr_text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime


# Score schemas
class RubricScore(BaseSchema):
    clarity: float = Field(..., ge=0, le=5, description="Clarity score (0-5)")
    structure: float = Field(..., ge=0, le=5, description="Structure score (0-5)")
    depth_specificity: float = Field(..., ge=0, le=5, description="Depth and specificity score (0-5)")
    role_fit: float = Field(..., ge=0, le=5, description="Role fit score (0-5)")
    technical: float = Field(..., ge=0, le=5, description="Technical score (0-5)")
    communication: float = Field(..., ge=0, le=5, description="Communication score (0-5)")
    ownership: float = Field(..., ge=0, le=5, description="Ownership score (0-5)")


class ScoreDetail(BaseSchema):
    scores: RubricScore
    rationale: str = Field(..., description="Scoring rationale")
    action_items: List[str] = Field(..., description="Action items for improvement")
    exemplar_snippet: Optional[str] = Field(None, description="Exemplar response snippet")
    meta: Optional[Dict[str, Any]] = None


class Score(BaseSchema):
    id: str
    answer_id: str
    rubric_json: ScoreDetail
    clarity: float
    structure: float
    depth_specificity: float
    role_fit: float
    technical: float
    communication: float
    ownership: float
    total_score: float
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime


# Report schemas
class ReportSummary(BaseSchema):
    overall_score: float = Field(..., ge=0, le=5, description="Overall session score")
    strengths: List[str] = Field(..., description="List of candidate strengths")
    areas_for_improvement: List[str] = Field(..., description="Areas needing improvement")
    recommendations: List[str] = Field(..., description="Recommendations for candidate")
    competency_breakdown: Dict[str, float] = Field(..., description="Scores by competency")


class Report(BaseSchema):
    id: str
    session_id: str
    report_json: ReportSummary
    pdf_url: Optional[str] = None
    summary: str
    overall_score: float
    strengths: List[str]
    areas_for_improvement: List[str]
    recommendations: List[str]
    created_at: datetime


# Artifact schemas
class ArtifactBase(BaseSchema):
    type: str = Field(..., description="Artifact type (cv, jd, company_brief)")
    path: str = Field(..., description="File path")


class ArtifactCreate(ArtifactBase):
    text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class Artifact(ArtifactBase):
    id: str
    text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime


# Upload schemas
class UploadResponse(BaseSchema):
    artifact_id: str
    type: str
    path: str
    message: str = "File uploaded successfully"


# Health check schema
class HealthResponse(BaseSchema):
    status: str = "healthy"
    timestamp: datetime
    services: Dict[str, str] = Field(..., description="Service health status")


# Error schemas
class ErrorResponse(BaseSchema):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Pagination schemas
class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
