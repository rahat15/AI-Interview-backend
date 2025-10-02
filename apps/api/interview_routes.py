from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from interview.session_manager import interview_manager

# Use versioned prefix
router = APIRouter(prefix="/v1/interview", tags=["Interview"])

# ---------------------------
# Request / Response Schemas
# ---------------------------

class StartSessionRequest(BaseModel):
    user_id: str
    session_id: str
    role_title: str
    company_name: str
    industry: str
    jd: Optional[str] = ""
    cv: Optional[str] = ""
    round_type: Optional[str] = "full"


class StartSessionResponse(BaseModel):
    session_id: str
    user_id: str
    first_question: str
    state: Dict[str, Any]


class AnswerRequest(BaseModel):
    user_id: str
    session_id: str
    answer: str


class AnswerResponse(BaseModel):
    evaluation: Optional[Dict[str, Any]]
    next_question: Optional[str]
    state: Dict[str, Any]


class ReportResponse(BaseModel):
    session_id: str
    user_id: str
    role: str
    company: str
    industry: str
    avg_scores: Dict[str, Any]
    history: List[Dict[str, Any]]

# ---------------------------
# Routes
# ---------------------------

@router.post("/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest):
    """
    Start a new interview session.
    Creates a session, initializes state, and returns the first question.
    """
    try:
        state = interview_manager.create_session(
            user_id=req.user_id,
            session_id=req.session_id,
            role_title=req.role_title,
            company_name=req.company_name,
            industry=req.industry,
            jd=req.jd,
            cv=req.cv,
            round_type=req.round_type,
        )

        # Advance graph until first question
        result = await interview_manager.step(req.user_id, req.session_id)

        return {
            "user_id": req.user_id,
            "session_id": req.session_id,
            "first_question": result.get("history", [])[-1]["question"],
            "state": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(req: AnswerRequest):
    """
    Submit an answer to the current question.
    Evaluates response, decides follow-up/transition, and returns next question.
    """
    try:
        result = await interview_manager.step(req.user_id, req.session_id, user_answer=req.answer)

        history = result.get("history", [])
        last = history[-1] if history else {}

        return {
            "evaluation": last.get("evaluation"),
            "next_question": None if result.get("end") else last.get("question"),
            "state": result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})


@router.get("/state/{user_id}/{session_id}")
def get_state(user_id: str, session_id: str):
    """
    Get the current interview state for a given session.
    """
    state = interview_manager.get_state(user_id, session_id)
    if not state:
        raise HTTPException(status_code=404, detail={"error": "Session not found"})
    return state


@router.get("/sessions/{user_id}")
def get_user_sessions(user_id: str):
    """
    Get all interview sessions for a specific user.
    """
    sessions = interview_manager.get_user_sessions(user_id)
    if not sessions:
        raise HTTPException(status_code=404, detail={"error": "No sessions found for user"})
    return sessions


@router.get("/report/{user_id}/{session_id}", response_model=ReportResponse)
def get_report(user_id: str, session_id: str):
    """
    Generate a structured summary report for an interview session.
    """
    report = interview_manager.generate_report(user_id, session_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report)
    return report
