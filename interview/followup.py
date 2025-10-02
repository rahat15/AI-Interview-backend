"""
interview/followup.py
Hybrid follow-up decision logic:
- Rule-based for clear cases
- LLM prompt for borderline/ambiguous answers
"""

import httpx
import os
import json
import logging
from ..prompts import FOLLOWUP_DECISION_PROMPT

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")


async def followup_decision(state: dict) -> dict:
    """
    Decide whether to ask a follow-up or move to next stage.
    Returns JSON: { "decision": "followup" | "stage_transition", "reason": str }
    """

    if not state.get("history"):
        return {"decision": "stage_transition", "reason": "No prior answers"}

    last_item = state["history"][-1]
    stage = state.get("stage")

    eval_data = last_item.get("evaluation", {})
    clarity = eval_data.get("clarity", 0)
    confidence = eval_data.get("confidence", 0)
    tech_depth = eval_data.get("technical_depth", 0)

    # 🚫 Never loop wrap-up stage
    if stage == "wrap-up":
        return {"decision": "stage_transition", "reason": "Wrap-up stage ends interview"}

    # ✅ Rule-based obvious cases
    if clarity <= 4 or confidence <= 4:
        return {"decision": "followup", "reason": "Low clarity or confidence"}
    if clarity >= 8 and confidence >= 8 and (stage != "technical" or tech_depth >= 7):
        return {"decision": "stage_transition", "reason": "Strong, clear response"}

    # 🤔 Borderline → Use LLM
    prompt = FOLLOWUP_DECISION_PROMPT.format(
        stage=stage,
        question=last_item.get("question", ""),
        answer=last_item.get("answer", ""),
        clarity=clarity,
        confidence=confidence,
        technical_depth=tech_depth
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 120,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            data = resp.json()
            logging.info("Groq follow-up decision: %s", data)

            raw_decision = data["choices"][0]["message"]["content"].strip()
            decision = json.loads(raw_decision)
            return decision
    except Exception as e:
        logging.exception("Follow-up LLM decision failed")
        # fallback: move forward
        return {"decision": "stage_transition", "reason": f"Fallback due to error: {e}"}
