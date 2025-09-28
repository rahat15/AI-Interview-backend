from fastapi import APIRouter, Request
from interview.session_manager import interview_manager
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

print("🔑 GROQ_API_KEY loaded?", os.getenv("GROQ_API_KEY") is not None)
print("🤖 LLM_MODEL:", os.getenv("LLM_MODEL"))


router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/start")
async def start_session(req: Request):
    body = await req.json()
    state = interview_manager.create_session(
        session_id=body["session_id"],
        role_title=body["role_title"],
        company_name=body["company_name"],
        industry=body["industry"],
        jd=body.get("jd", ""),
        cv=body.get("cv", ""),
        stage=body.get("stage", "intro")
    )
    q = await interview_manager.get_next_question(body["session_id"])
    return {"question": q, "state": state}


@router.post("/answer")
async def submit_answer(req: Request):
    body = await req.json()
    session_id = body["session_id"]
    answer_text = body["answer"]

    eval_result = await interview_manager.submit_answer(session_id, answer_text)
    next_q = None
    state = interview_manager.get_state(session_id)

    if state["should_follow_up"]:
        next_q = await interview_manager.get_next_question(session_id)

    return {
        "evaluation": eval_result,
        "next_question": next_q,
        "state": state
    }


@router.post("/next")
async def next_question(req: Request):
    body = await req.json()
    q = await interview_manager.get_next_question(body["session_id"])
    return {"question": q}


@router.post("/stage")
async def change_stage(req: Request):
    body = await req.json()
    state = interview_manager.advance_stage(body["session_id"], body["new_stage"])
    q = await interview_manager.get_next_question(body["session_id"])
    return {"new_stage": body["new_stage"], "question": q, "state": state}


@router.get("/report/{session_id}")
def get_report(session_id: str):
    return interview_manager.generate_report(session_id)
