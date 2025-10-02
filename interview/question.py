import httpx
import os
import logging
from .stages import (
    intro_stage, hr_stage, technical_stage,
    behavioral_stage, managerial_stage, wrapup_stage,
)
from .prompts import BASE_QUESTION_PROMPT, FOLLOWUP_INSTRUCTIONS

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# Stage map → functions for instructions
STAGE_MAP = {
    "intro": intro_stage,
    "hr": hr_stage,
    "technical": technical_stage,
    "behavioral": behavioral_stage,
    "managerial": managerial_stage,
    "wrap-up": wrapup_stage,
}


async def generate_question(state, stage: str, followup: bool = False) -> str:
    """
    Generate a professional interview question for the given stage using Groq API.
    """

    # 1. Get stage-specific instruction
    stage_info = STAGE_MAP.get(stage, lambda s: {"instruction": "Ask a relevant interview question."})(state)
    stage_instruction = stage_info["instruction"]

    # 2. Prepare history context (last 2-3 exchanges only)
    history_context = state["history"][-3:] if state.get("history") else "None"

    # 3. Build prompt
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
        followup_instructions=FOLLOWUP_INSTRUCTIONS if followup else ""
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt.strip()}],
        "temperature": 0.6,  # keep it professional, less creative
        "max_tokens": 200,
    }

    # 4. Call Groq API
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            data = resp.json()

            logging.info("Groq response (question): %s", data)

            if "choices" not in data:
                error_msg = data.get("error", {}).get("message", "Unknown error from Groq")
                logging.error("Groq API error: %s", error_msg)
                return f"(Error generating question: {error_msg})"

            question = data["choices"][0]["message"]["content"].strip()
            return question

    except Exception as e:
        logging.exception("Exception in generate_question")
        return f"(Error generating question: {str(e)})"
