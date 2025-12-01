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
    Determine whether to ask a follow-up or transition stages.
    Returns: { "decision": "followup" | "stage_transition", "reason": str }
    """

    history = state.get("history", [])
    stage = state.get("stage", "intro")

    # No history means always proceed
    if not history:
        return {"decision": "stage_transition", "reason": "No prior responses"}

    last = history[-1]

    # Extract evaluation values safely
    eval_data = last.get("evaluation") or {}
    clarity = int(eval_data.get("clarity", 0))
    confidence = int(eval_data.get("confidence", 0))
    tech_depth = int(eval_data.get("technical_depth", 0))

    # ------------------------------------------
    # ⚠ RULE-BASED QUICK DECISIONS
    # ------------------------------------------

    # If user gave no real answer
    if not last.get("answer"):
        return {"decision": "followup", "reason": "Blank answer"}

    # Never loop wrap-up
    if stage == "wrap-up":
        return {"decision": "stage_transition", "reason": "Wrap-up ends interview"}

    # Weak, vague, unclear
    if clarity <= 4 or confidence <= 4:
        return {"decision": "followup", "reason": "Low clarity/confidence"}

    # Very strong answer
    if clarity >= 8 and confidence >= 8 and (stage != "technical" or tech_depth >= 7):
        return {"decision": "stage_transition", "reason": "Strong answer"}

    # ------------------------------------------
    # 🤔 Borderline → Use LLM
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

        logger.info("Groq followup response: %s", data)

        if "error" in data:
            return {"decision": "stage_transition", "reason": "Groq error fallback"}

        raw = data["choices"][0]["message"]["content"].strip()
        decision = safe_parse_json(raw)

        # Validate decision format
        if decision.get("decision") not in ["followup", "stage_transition"]:
            return {"decision": "stage_transition", "reason": "Invalid model output"}

        return decision

    except Exception as e:
        logger.exception("Follow-up LLM failed")
        return {"decision": "stage_transition", "reason": f"Error: {str(e)}"}
