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
from .prompts import BASE_QUESTION_PROMPT, FOLLOWUP_INSTRUCTIONS

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
    """Reduce history to last 2 turns for prompt."""
    if not history:
        return "None"

    short = history[-2:]
    simple = [
        {"q": h.get("question"), "a": h.get("answer") or ""}
        for h in short
    ]
    return simple


async def generate_question(state, stage: str, followup: bool = False) -> str:
    """
    Generate a question for the interview stage.
    Returns a clean, concise question string.
    """

    # 1. Stage instructions
    stage_fn = STAGE_MAP.get(stage)
    if not stage_fn:
        stage_instruction = "Ask a relevant and concise interview question."
    else:
        stage_instruction = stage_fn(state)["instruction"]

    # 2. Short history
    history_context = _short_history(state.get("history"))

    # 3. Build formatted prompt
    prompt = BASE_QUESTION_PROMPT.format(
        role=state["config"]["role_title"],
        company=state["config"]["company_name"],
        industry=state["config"]["industry"],
        stage=stage,
        stage_instruction=stage_instruction,
        experience=state["config"].get("experience", ""),
        jd=state["jd"],
        cv=state["cv"],
        history=history_context,
        followup_instructions=FOLLOWUP_INSTRUCTIONS if followup else "",
    ).strip()

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

    # 4. Call Groq API
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            data = resp.json()

        logger.info("Groq question response: %s", data)

        # API error
        if "error" in data:
            msg = data["error"].get("message", "Unknown Groq error")
            return f"(Groq error: {msg})"

        # No choices → bad response
        if "choices" not in data or not data["choices"]:
            return "(Error: Groq returned no question.)"

        content = data["choices"][0]["message"]["content"].strip()

        # Clean any extra content — keep only first question-like sentence
        clean = content.split("\n")[0].strip()
        clean = clean.replace("Sure,", "").replace("Here's a question:", "").strip()

        return clean

    except Exception as e:
        logger.exception("Exception in generate_question()")
        return f"(Error generating question: {str(e)})"
