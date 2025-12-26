from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed, Link
from pydantic import Field
from pymongo import IndexModel, TEXT
from bson import ObjectId
import uuid


class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: Indexed(str, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        name = "users"


class Resume(Document):
    filename: str
    path: str
    stats: Dict[str, Any]
    improvement_resume: Optional[Dict[str, Any]] = None
    user: str  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    version: int = Field(default=0, alias="__v")

    class Settings:
        name = "resumes"
        use_state_management = True


class JobDescription(Document):
    filename: str
    path: str
    text: Optional[str] = None
    user: str  # User ID
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=datetime.utcnow, alias="updatedAt")
    version: int = Field(default=0, alias="__v")

    class Settings:
        name = "jobdescriptions"


class Artifact(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    type: str  # cv, jd, company_brief
    path: str
    text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "artifacts"


class Session(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    role: str
    industry: str
    company: str
    status: str = "planning"  # planning, active, completed, failed
    plan_json: Optional[Dict[str, Any]] = None
    cv_file_id: Optional[str] = None
    jd_file_id: Optional[str] = None
    current_question_index: int = 0
    total_questions: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "sessions"


class Question(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    session_id: str
    competency: str  # technical, behavioral, etc.
    difficulty: str = "medium"  # easy, medium, hard
    text: str
    meta: Optional[Dict[str, Any]] = None
    order_index: int
    is_follow_up: bool = False
    parent_question_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "questions"


class Answer(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    session_id: str
    question_id: str
    text: Optional[str] = None
    audio_url: Optional[str] = None
    asr_text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "answers"


class Score(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    answer_id: str
    rubric_json: Dict[str, Any]
    clarity: float
    structure: float
    depth_specificity: float
    role_fit: float
    technical: float
    communication: float
    ownership: float
    total_score: float
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "scores"


class Report(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    session_id: Indexed(str, unique=True)
    report_json: Dict[str, Any]
    pdf_url: Optional[str] = None
    summary: Optional[str] = None
    overall_score: Optional[float] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "reports"


class Embedding(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    artifact_id: str
    chunk_idx: int
    content: str
    embedding: List[float]  # Vector embeddings as list of floats
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "embeddings"
        indexes = [
            IndexModel([("artifact_id", 1), ("chunk_idx", 1)]),
            IndexModel([("content", TEXT)])
        ]