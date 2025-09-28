# apps/api/routers/interview.py
import os
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from groq import Groq

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/interview", tags=["interview"])

# Load env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

client = Groq(api_key=GROQ_API_KEY)


# ── Data Models ───────────────────────────────────────────────
class InterviewStartRequest(BaseModel):
    session_id: str
    role_title: str
    company_name: str
    industry: Optional[str] = None
    jd: str
    cv: str


class InterviewResponseRequest(BaseModel):
    session_id: str
    user_answer: str


class InterviewState(BaseModel):
    session_id: str
    config: Dict[str, Any]
    jd: str
    cv: str
    stage: str
    history: List[Dict[str, Any]]
    should_follow_up: bool
    completed: bool


# ── In-memory store (replace with Redis/DB later) ──────────────
SESSIONS: Dict[str, InterviewState] = {}


# ── Helpers ───────────────────────────────────────────────────
def generate_question(prompt: str) -> str:
    """Call Groq API to generate a question from prompt."""
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional interviewer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return f"(Error generating question: {e})"


# ── Routes ────────────────────────────────────────────────────
@router.post("/start")
async def start_interview(req: InterviewStartRequest):
    """Initialize interview session and return the first question."""

    intro_prompt = (
        f"You are interviewing a candidate for the role of {req.role_title} "
        f"at {req.company_name} in the {req.industry or 'general'} industry.\n\n"
        f"Job description: {req.jd}\n\n"
        f"Candidate CV: {req.cv}\n\n"
        f"Start the interview by asking an introductory question."
    )

    first_question = generate_question(intro_prompt)

    state = InterviewState(
        session_id=req.session_id,
        config={
            "role_title": req.role_title,
            "company_name": req.company_name,
            "industry": req.industry,
        },
        jd=req.jd,
        cv=req.cv,
        stage="intro",
        history=[{"q": first_question, "a": None, "eval": None}],
        should_follow_up=False,
        completed=False,
    )

    SESSIONS[req.session_id] = state

    return {"question": first_question, "state": state.dict()}


@router.post("/respond")
async def respond_interview(req: InterviewResponseRequest):
    """Handle candidate’s answer and generate follow-up or next question."""
    state = SESSIONS.get(req.session_id)
    if not state:
        return {"error": "Session not found"}

    # Get last question
    last_q = state.history[-1]["q"]

    # Store user’s answer
    state.history[-1]["a"] = req.user_answer

    # Ask model whether to follow up or move on
    followup_prompt = (
        f"Previous question: {last_q}\n"
        f"Candidate answer: {req.user_answer}\n\n"
        "Decide whether to ask a follow-up question (if the answer is incomplete) "
        "or move to the next relevant interview question. Just output the next question."
    )

    next_question = generate_question(followup_prompt)

    state.history.append({"q": next_question, "a": None, "eval": None})
    state.stage = "ongoing"
    SESSIONS[state.session_id] = state

    return {"question": next_question, "state": state.dict()}
