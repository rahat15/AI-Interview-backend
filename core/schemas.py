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


# V2 Interview Schemas (Gemini-based)
class InterviewV2StartRequest(BaseSchema):
    resume_text: Optional[str] = Field(None, description="Resume content (full text) - optional if file uploaded")
    jd_text: Optional[str] = Field(None, description="Job Description content (full text) - optional if file uploaded")
    role: str = Field(..., description="Job role/position")
    company: str = Field(default="the company", description="Company name")


class InterviewV2StartResponse(BaseSchema):
    session_id: str
    status: str
    question: str
    question_number: int
    message: str = "Interview started successfully"


class InterviewV2AnswerRequest(BaseSchema):
    answer: str = Field(..., description="Candidate's answer to the question")


class InterviewV2AnswerResponse(BaseSchema):
    session_id: str
    status: str
    question: str
    question_number: int


class VideoAnalytics(BaseSchema):
    confidence_score: float
    eye_contact_percentage: int
    posture_score: float
    engagement_level: str
    speech_pace: str
    filler_words_count: int
    smile_frequency: str
    facial_expressions: Dict[str, int]
    body_language: Dict[str, int]
    energy_level: str
    professionalism_score: float


class SkillAssessment(BaseSchema):
    score: float
    assessment: str


class InterviewEvaluation(BaseSchema):
    overall_score: float
    recommendation: str
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    technical_skills: SkillAssessment
    communication_skills: SkillAssessment
    problem_solving: SkillAssessment
    cultural_fit: SkillAssessment
    experience_relevance: SkillAssessment
    detailed_feedback: str
    improvement_areas: List[str]
    key_highlights: List[str]


class ConversationTurn(BaseSchema):
    role: str
    content: str


class InterviewV2CompleteResponse(BaseSchema):
    session_id: str
    status: str
    interview_duration_minutes: int
    total_questions: int
    role: str
    company: str
    evaluation: InterviewEvaluation
    video_analytics: VideoAnalytics
    conversation: List[ConversationTurn]
    metrics: Dict[str, float]


# Resume optimization schemas
class CVQualitySubscore(BaseSchema):
    dimension: str
    score: int
    max_score: int
    evidence: List[str]


class CVQuality(BaseSchema):
    overall_score: int
    subscores: List[CVQualitySubscore]


class JDMatchSubscore(BaseSchema):
    dimension: str
    score: int
    max_score: int
    evidence: List[str]


class JDMatch(BaseSchema):
    overall_score: int
    subscores: List[JDMatchSubscore]


class KeyTakeaways(BaseSchema):
    red_flags: List[str]
    green_flags: List[str]


class Analytics(BaseSchema):
    cv_quality: CVQuality
    jd_match: JDMatch
    key_takeaways: KeyTakeaways
    overall_score: int


class TailoredResume(BaseSchema):
    summary: str
    experience: List[str]
    skills: List[str]
    projects: List[str]


class Top1PercentGap(BaseSchema):
    strengths: List[str]
    gaps: List[str]
    actionable_next_steps: List[str]


class Enhancement(BaseSchema):
    tailored_resume: TailoredResume
    top_1_percent_gap: Top1PercentGap
    cover_letter: str


class ResumeData(BaseSchema):
    id: str
    filename: str
    url: str
    analytics: Analytics
    enhancement: Enhancement


class ResumeAnalysisRequest(BaseSchema):
    message: Optional[str] = None
    resume: Optional[ResumeData] = None
    # Support direct fields as well (for backward compatibility)
    id: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    analytics: Optional[Analytics] = None
    enhancement: Optional[Enhancement] = None


class OptimizedCVContent(BaseSchema):
    professional_summary: str
    key_skills: List[str]
    experience_highlights: List[str]
    project_descriptions: List[str]
    achievements: List[str]
    recommendations: List[str]
    cover_letter_template: str
    ats_keywords: List[str]
    improvement_priority: List[str]


class CVOptimizationResponse(BaseSchema):
    status: str
    optimized_content: OptimizedCVContent
    confidence_score: float
    message: str


class ResumeBuilderContent(BaseSchema):
    personal_info: Dict[str, str]
    professional_summary: str
    skills: Dict[str, List[str]]
    experience: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    achievements: List[str]
    certifications: List[Dict[str, str]]
    languages: List[Dict[str, str]]


class ResumeBuilderResponse(BaseSchema):
    status: str
    resume_content: ResumeBuilderContent
    formatting_tips: List[str]
    message: str


# Separate schema for JSON-based start (resume/jd as text)
# Note: JSON/text-only start schema removed to avoid duplicate OpenAPI
# exposure. The multipart `/v2/interview/start` endpoint should be used
# for file uploads (PDF/DOCX/TXT). A hidden JSON start endpoint exists
# in the router for non-OpenAPI use-cases.
