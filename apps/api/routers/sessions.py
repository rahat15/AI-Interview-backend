from typing import List
from fastapi import APIRouter, HTTPException, status
import uuid

# REMOVE DB imports
# from core.db import get_db
# from core.models import User, Session as SessionModel, Question, Answer, Report
# from apps.api.deps.auth import get_current_active_user
# from interview.graph import InterviewGraph
# from apps.worker.jobs import enqueue_scoring_job

from core.schemas import (
    SessionCreate,
    Session as SessionSchema,
    NextQuestionResponse,
    AnswerCreate,
    Report as ReportSchema,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

# --- In-memory storage (since no DB) ---
_sessions = {}
_questions = {}
_answers = {}
_reports = {}

# --------- Endpoints ---------

@router.post("/", response_model=SessionSchema)
async def create_session(session_in: SessionCreate):
    """Create a new interview session (mocked, no DB)."""
    session_id = uuid.uuid4()
    fake_session = {
        "id": session_id,
        "role": session_in.role,
        "industry": session_in.industry,
        "company": session_in.company,
        "cv_file_id": session_in.cv_file_id,
        "jd_file_id": session_in.jd_file_id,
        "status": "active",
        "current_question_index": 0,
    }
    _sessions[session_id] = fake_session

    # Optionally attach dummy questions
    _questions[session_id] = [
        {"id": uuid.uuid4(), "text": "Tell me about yourself", "order_index": 0, "competency": "intro", "difficulty": "easy", "meta": {}},
        {"id": uuid.uuid4(), "text": "What is your biggest strength?", "order_index": 1, "competency": "strength", "difficulty": "medium", "meta": {}},
    ]
    return fake_session


@router.get("/{session_id}", response_model=SessionSchema)
async def get_session(session_id: uuid.UUID):
    if session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _sessions[session_id]


@router.get("/", response_model=List[SessionSchema])
async def list_sessions():
    return list(_sessions.values())


@router.get("/{session_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(session_id: uuid.UUID):
    if session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session = _sessions[session_id]
    idx = session["current_question_index"]

    if idx >= len(_questions.get(session_id, [])):
        session["status"] = "completed"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No more questions - session completed")

    q = _questions[session_id][idx]
    return NextQuestionResponse(
        question_id=q["id"],
        text=q["text"],
        competency=q["competency"],
        difficulty=q["difficulty"],
        meta=q["meta"],
    )


@router.post("/{session_id}/answer")
async def submit_answer(session_id: uuid.UUID, answer_in: AnswerCreate):
    if session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session = _sessions[session_id]
    idx = session["current_question_index"]

    if idx >= len(_questions.get(session_id, [])):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending question to answer")

    # Record fake answer
    ans_id = uuid.uuid4()
    _answers[ans_id] = {
        "id": ans_id,
        "session_id": session_id,
        "question_id": answer_in.question_id,
        "text": answer_in.text,
        "audio_url": answer_in.audio_url,
    }

    # Move to next question
    session["current_question_index"] += 1
    return {"message": "Answer submitted successfully", "answer_id": ans_id, "next_question_index": session["current_question_index"]}


@router.get("/{session_id}/report", response_model=ReportSchema)
async def get_session_report(session_id: uuid.UUID):
    if session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Return dummy report
    return ReportSchema(
        session_id=session_id,
        json={"summary": "Mock summary", "overall_score": 85},
        summary="Great performance overall",
        overall_score=85.0,
        strengths=["Communication", "Problem solving"],
        areas_for_improvement=["Conciseness"],
        recommendations=["Practice STAR method"]
    )


@router.delete("/{session_id}")
async def delete_session(session_id: uuid.UUID):
    if session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    _sessions.pop(session_id, None)
    _questions.pop(session_id, None)
    _reports.pop(session_id, None)
    return {"message": "Session deleted successfully"}
