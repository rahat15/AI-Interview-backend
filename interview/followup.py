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

# Groq API config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

MAX_FOLLOWUPS = {
    "intro": 1,
    "hr": 1,
    "behavioral": 1,
    "managerial": 1,
    "wrap-up": 0,
    "technical": 2,
}


# -----------------------------------------------------------
# SAFE PARSER (LLM output → JSON)
# -----------------------------------------------------------
def safe_parse_json(text: str) -> dict:
    """
    Robust JSON parsing for LLM responses.
    - Removes non-JSON prefixes/suffixes
    - Tries multiple fallback attempts
    """
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to extract JSON substring
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        pass

    # Final fallback
    return {
        "decision": "stage_transition",
        "reason": "Invalid JSON from LLM"
    }


# -----------------------------------------------------------
# MAIN FUNCTION — used by LangGraph
# -----------------------------------------------------------
async def followup_decision(state: dict) -> dict:
    """
    Determine whether to ask a follow-up or transition to the next stage.
    Enforces stage-based follow-up limits and prevents infinite loops.
    """

    history = state.get("history", [])
    stage = state.get("stage", "intro")

    # No history → move on
    if not history:
        return {"decision": "stage_transition", "reason": "No prior responses"}

    last = history[-1]

    # Extract evaluation safely
    eval_data = last.get("evaluation") or {}
    clarity = int(eval_data.get("clarity", 0))
    confidence = int(eval_data.get("confidence", 0))
    tech_depth = int(eval_data.get("technical_depth", 0))

    # ------------------------------------------
    # 🔒 STAGE-BASED FOLLOWUP LIMITS
    # ------------------------------------------
    MAX_FOLLOWUPS = {
        "intro": 1,
        "hr": 1,
        "behavioral": 1,
        "managerial": 1,
        "wrap-up": 0,
        "technical": 2,
    }

    # Count recent follow-ups
    recent_fups = 0
    for h in reversed(history):
        if h.get("is_followup"):
            recent_fups += 1
        else:
            break

    if recent_fups >= MAX_FOLLOWUPS.get(stage, 1):
        return {"decision": "stage_transition", "reason": "Follow-up limit reached"}

    # ------------------------------------------
    # 🛑 Wrap-up stage never loops
    # ------------------------------------------
    if stage == "wrap-up":
        return {"decision": "stage_transition", "reason": "End of interview"}

    # ------------------------------------------
    # 🧹 Stage-specific adjustments
    # ------------------------------------------

    # Non-technical stages ignore technical depth entirely
    if stage != "technical":
        tech_depth = 10  # treat as "good enough"

    # Blank answer → follow-up
    if not last.get("answer"):
        return {"decision": "followup", "reason": "Blank answer"}

    # Weak clarity or confidence → follow-up
    if clarity <= 4 or confidence <= 4:
        return {"decision": "followup", "reason": "Low clarity/confidence"}

    # Strong answer → move on
    if clarity >= 7 and confidence >= 7:
        if stage == "technical" and tech_depth < 6:
            # strong communication but weak technical detail → follow-up allowed
            pass
        else:
            return {"decision": "stage_transition", "reason": "Strong answer"}

    # ------------------------------------------
    # 🤔 Borderline → Ask LLM to decide
    # ------------------------------------------
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

        # Validate structured output
        if decision.get("decision") not in ["followup", "stage_transition"]:
            return {"decision": "stage_transition", "reason": "Invalid model output"}

        # Hard-enforce follow-up limit again after model decision
        if decision["decision"] == "followup" and recent_fups + 1 > MAX_FOLLOWUPS[stage]:
            return {"decision": "stage_transition", "reason": "Follow-up limit reached"}

        return decision

    except Exception as e:
        logger.exception("Follow-up LLM failed")
        return {"decision": "stage_transition", "reason": f"Error: {str(e)}"}
