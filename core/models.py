from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

from .db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(255), nullable=False)
    industry = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    status = Column(String(50), default="planning")  # planning, active, completed, failed
    plan_json = Column(JSON)
    cv_file_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=True)
    jd_file_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=True)
    current_question_index = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    cv_artifact = relationship("Artifact", foreign_keys=[cv_file_id])
    jd_artifact = relationship("Artifact", foreign_keys=[jd_file_id])
    questions = relationship("Question", back_populates="session")
    answers = relationship("Answer", back_populates="session")
    report = relationship("Report", back_populates="session", uselist=False)


class Artifact(Base):
    __tablename__ = "artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)  # cv, jd, company_brief
    path = Column(String(500), nullable=False)
    text = Column(Text)
    meta = Column(JSON)  # normalized data, file info, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sessions_as_cv = relationship("Session", foreign_keys=[Session.cv_file_id])
    sessions_as_jd = relationship("Session", foreign_keys=[Session.jd_file_id])
    embeddings = relationship("Embedding", back_populates="artifact")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    competency = Column(String(100), nullable=False)  # technical, behavioral, etc.
    difficulty = Column(String(50), default="medium")  # easy, medium, hard
    text = Column(Text, nullable=False)
    meta = Column(JSON)  # expected_signals, pitfalls, etc.
    order_index = Column(Integer, nullable=False)
    is_follow_up = Column(Boolean, default=False)
    parent_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="questions")
    parent_question = relationship("Question", remote_side=[id])
    follow_ups = relationship("Question", back_populates="parent_question")
    answers = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    text = Column(Text)
    audio_url = Column(String(500))
    asr_text = Column(Text)  # Speech-to-text result
    meta = Column(JSON)  # processing info, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    scores = relationship("Score", back_populates="answer")


class Score(Base):
    __tablename__ = "scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=False)
    rubric_json = Column(JSON, nullable=False)  # Detailed scoring breakdown
    clarity = Column(Float, nullable=False)
    structure = Column(Float, nullable=False)
    depth_specificity = Column(Float, nullable=False)
    role_fit = Column(Float, nullable=False)
    technical = Column(Float, nullable=False)
    communication = Column(Float, nullable=False)
    ownership = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    meta = Column(JSON)  # evaluation metadata, timing, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    answer = relationship("Answer", back_populates="scores")


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, unique=True)
    json = Column(JSON, nullable=False)  # Complete report data
    pdf_url = Column(String(500))
    summary = Column(Text)
    overall_score = Column(Float)
    strengths = Column(JSON)  # List of strengths
    areas_for_improvement = Column(JSON)  # List of improvement areas
    recommendations = Column(JSON)  # List of recommendations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="report")


class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    chunk_idx = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # pgvector column for embeddings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    artifact = relationship("Artifact", back_populates="embeddings")
    
    __table_args__ = (
        # Index for vector similarity search
        {"postgresql_using": "ivfflat"}
    )
