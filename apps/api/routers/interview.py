# apps/api/routers/interview.py

import os
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Try Groq safely
try:
    from groq import Groq
except ImportError:
    Groq = None

# Load env
load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/interview", tags=["Interview"])

# ── Environment ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

client = None
if GROQ_API_KEY and Groq:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ Groq client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to init Groq client: {e}", exc_info=True)

# ── Data Models ─────────────────────────────────────────────
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


# ── In-memory session store (replace later with Redis/DB) ────
SESSIONS: Dict[str, InterviewState] = {}


# ── Helpers ─────────────────────────────────────────────────
def generate_question(prompt: str) -> str:
    """Call Groq API to generate a question from prompt."""
    if not client:
        return "(Error: Groq client not initialized. Missing GROQ_API_KEY.)"

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional interviewer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        if not response.choices:
            return "(Error: No choices returned from LLM)"
        
        # ✅ Fix: ChatCompletionMessage is an object, not a dict
        content = getattr(response.choices[0].message, "content", None)
        if not content:
            return "(Error: Empty response from LLM)"
        return content.strip()

    except Exception as e:
        logger.error(f"LLM error: {e}", exc_info=True)
        return f"(Error generating question: {e})"



# ── Endpoints ───────────────────────────────────────────────

@router.post("/start")
async def start_interview(req: InterviewStartRequest):
    """Initialize interview session and return the first question."""
    intro_prompt = (
        f"You are interviewing a candidate for the role of {req.role_title} "
        f"at {req.company_name} in the {req.industry or 'general'} industry.\n\n"
        f"Job description:\n{req.jd}\n\n"
        f"Candidate CV:\n{req.cv}\n\n"
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
        raise HTTPException(status_code=404, detail="Session not found")

    last_q = state.history[-1]["q"]
    state.history[-1]["a"] = req.user_answer

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


@router.post("/answer")
async def submit_answer(req: Request):
    """Legacy endpoint: submit answer & optionally get follow-up question."""
    body = await req.json()
    session_id = body["session_id"]
    answer_text = body["answer"]

    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # reuse logic
    state.history[-1]["a"] = answer_text
    followup_prompt = (
        f"Previous question: {state.history[-1]['q']}\n"
        f"Candidate answer: {answer_text}\n\n"
        "Evaluate briefly, then suggest next question."
    )
    next_q = generate_question(followup_prompt)
    state.history.append({"q": next_q, "a": None, "eval": None})
    state.stage = "ongoing"

    return {"evaluation": "(mock eval)", "next_question": next_q, "state": state.dict()}


@router.post("/next")
async def next_question(req: Request):
    body = await req.json()
    session_id = body["session_id"]
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    q = generate_question("Ask the next interview question.")
    state.history.append({"q": q, "a": None, "eval": None})
    return {"question": q, "state": state.dict()}


@router.post("/stage")
async def change_stage(req: Request):
    body = await req.json()
    session_id = body["session_id"]
    new_stage = body["new_stage"]
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    state.stage = new_stage
    q = generate_question(f"Now move to the {new_stage} stage. Ask next question.")
    state.history.append({"q": q, "a": None, "eval": None})
    return {"new_stage": new_stage, "question": q, "state": state.dict()}


@router.get("/report/{session_id}")
def get_report(session_id: str):
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "stage": state.stage,
        "questions": state.history,
        "completed": state.completed,
    }
