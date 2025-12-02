import httpx
import os
import logging

from .stages import (
    intro_stage,
    hr_stage,
    technical_stage,
    behavioral_stage,
    managerial_stage,
    wrapup_stage,
)
from interview.prompts import BASE_QUESTION_PROMPT, FOLLOWUP_INSTRUCTIONS, STRICT_STAGE_INSTRUCTIONS

logger = logging.getLogger(__name__)

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# Stage-to-function map
STAGE_MAP = {
    "intro": intro_stage,
    "hr": hr_stage,
    "technical": technical_stage,
    "behavioral": behavioral_stage,
    "managerial": managerial_stage,
    "wrap-up": wrapup_stage,
}


def _short_history(history):
    """
    Reduce history to the last 3 turns and format as text.
    """
    if not history:
        return "None"

    # Limit to last 3 exchanges to keep context focused
    short = history[-3:]
    
    # Format as a clean string block
    formatted = []
    for h in short:
        q_text = h.get("question", "")
        a_text = h.get("answer") or "(No answer)"
        formatted.append(f"Interviewer: {q_text}\nCandidate: {a_text}")
    
    return "\n\n".join(formatted)


async def generate_question(state, stage: str, followup: bool = False) -> str:
    """
    Generate a question for the interview stage.
    """
    
    # 1. Get Session Config (Safely)
    # This prevents KeyError if session_config is missing
    config = state.get("session_config", {})

    # 2. Stage instructions
    stage_fn = STAGE_MAP.get(stage)
    if not stage_fn:
        stage_instruction = "Ask a relevant and concise interview question."
    else:
        stage_instruction = stage_fn(state)["instruction"]

    # 3. Short history
    history_context = _short_history(state.get("history"))

    # 4. Build formatted prompt
    # --- FIX: Read from 'config' variable safely ---
    try:
        prompt = BASE_QUESTION_PROMPT.format(
            role=config.get("role_title", "Role"),
            company=config.get("company_name", "Company"),
            industry=config.get("industry", "Industry"),
            stage=stage,
            stage_instruction = STRICT_STAGE_INSTRUCTIONS.get(stage, "Ask a relevant question."),
            experience=config.get("experience", ""),
            jd=config.get("jd", ""),   # <--- FIX: Read from config
            cv=config.get("cv", ""),   # <--- FIX: Read from config
            history=history_context,
            followup_instructions=FOLLOWUP_INSTRUCTIONS if followup else "",
        ).strip()
    except KeyError as e:
        logger.error(f"Missing key in prompt formatting: {e}")
        return "(Error: Prompt formatting failed. Check config.)"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 200,
    }

    # 5. Call Groq API
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            data = resp.json()

        logger.info("Groq question response: %s", data)

        if "error" in data:
            msg = data["error"].get("message", "Unknown Groq error")
            return f"(Groq error: {msg})"

        if "choices" not in data or not data["choices"]:
            return "(Error: Groq returned no question.)"

        content = data["choices"][0]["message"]["content"].strip()
        clean = content.split("\n")[0].strip()
        clean = clean.replace("Sure,", "").replace("Here's a question:", "").strip()

        return clean

    except Exception as e:
        logger.exception("Exception in generate_question()")
        return f"(Error generating question: {str(e)})"