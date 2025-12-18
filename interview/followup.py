"""
interview/followup.py
Hybrid rule-based + LLM decision for follow-up vs stage transition.
"""

import os
import httpx
import json
import logging
from interview.prompts import FOLLOWUP_DECISION_PROMPT

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Groq API Config
# --------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# --------------------------------------------------
# Follow-up limits per stage
# --------------------------------------------------
MAX_FOLLOWUPS = {
    "intro": 1,
    "hr": 1,
    "behavioral": 1,
    "managerial": 1,
    "wrap-up": 0,
    "technical": 2,
}


def safe_parse_json(text: str) -> dict:
    """
    Robust JSON parsing for LLM output.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        pass

    return {"decision": "stage_transition", "reason": "Invalid JSON from LLM"}


async def followup_decision(state: dict) -> dict:
    """
    Decide whether to ask a follow-up or move to the next stage.
    """

    history = state.get("history", [])
    stage = state.get("stage", "intro")

    if not history:
        return {"decision": "stage_transition", "reason": "No prior response"}

    last = history[-1]
    evaluation = last.get("evaluation", {}) or {}

    clarity = int(evaluation.get("clarity", 0))
    confidence = int(evaluation.get("confidence", 0))
    tech_depth = int(evaluation.get("technical_depth", 0))

    # --------------------------------------------------
    # Count recent follow-ups
    # --------------------------------------------------
    recent_fups = 0
    for h in reversed(history):
        if h.get("is_followup"):
            recent_fups += 1
        else:
            break

    if recent_fups >= MAX_FOLLOWUPS.get(stage, 1):
        return {"decision": "stage_transition", "reason": "Follow-up limit reached"}

    if stage == "wrap-up":
        return {"decision": "stage_transition", "reason": "End of interview"}

    # Non-technical stages ignore technical depth
    if stage != "technical":
        tech_depth = 10

    # Blank answer
    if not last.get("answer"):
        return {"decision": "followup", "reason": "Blank answer"}

    # Low clarity or confidence
    if clarity <= 4 or confidence <= 4:
        return {"decision": "followup", "reason": "Low clarity or confidence"}

    # Strong answer → move on (unless technical depth weak)
    if clarity >= 7 and confidence >= 7:
        if stage != "technical" or tech_depth >= 6:
            return {"decision": "stage_transition", "reason": "Strong answer"}

    # --------------------------------------------------
    # Borderline → LLM decides
    # --------------------------------------------------
    prompt = FOLLOWUP_DECISION_PROMPT.format(
        stage=stage,
        question=last.get("question", ""),
        answer=last.get("answer", ""),
        clarity=clarity,
        confidence=confidence,
        technical_depth=tech_depth,
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 80,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            data = resp.json()

        if "error" in data:
            return {"decision": "stage_transition", "reason": "Groq error fallback"}

        raw = data["choices"][0]["message"]["content"].strip()
        decision = safe_parse_json(raw)

        if decision.get("decision") not in ("followup", "stage_transition"):
            return {"decision": "stage_transition", "reason": "Invalid model output"}

        if (
            decision["decision"] == "followup"
            and recent_fups + 1 > MAX_FOLLOWUPS.get(stage, 1)
        ):
            return {"decision": "stage_transition", "reason": "Follow-up limit reached"}

        return decision

    except Exception as e:
        logger.exception("Follow-up decision failed")
        return {"decision": "stage_transition", "reason": f"Error: {str(e)}"}
