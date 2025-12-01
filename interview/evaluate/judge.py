"""
interview/evaluate/judge.py
Evaluates a candidate's answer using Groq.
Returns clean, consistent JSON required by LangGraph.
"""

import os
import httpx
import json
import logging
from interview.prompts import BASE_EVALUATION_PROMPT

logger = logging.getLogger(__name__)

# Groq config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")


# ---------------------------------------------------------
# Safe JSON extraction
# ---------------------------------------------------------
def safe_json(text: str):
    """Extract valid JSON, even if wrapped in other text."""
    try:
        return json.loads(text)
    except Exception:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except Exception:
            return {"error": "Malformed JSON", "raw": text}


# ---------------------------------------------------------
# MAIN FUNCTION — this is what LangGraph calls
# ---------------------------------------------------------
async def evaluate_answer(user_answer: str, jd: str, cv: str, stage: str = "general") -> dict:
    """
    Evaluate a candidate's answer using LLM.
    ALWAYS returns JSON with required keys:
      clarity, confidence, technical_depth, summary
    """

    if not user_answer:
        return {
            "clarity": 0,
            "confidence": 0,
            "technical_depth": 0,
            "summary": "No answer provided."
        }

    prompt = BASE_EVALUATION_PROMPT.format(
        stage=stage,
        question="(handled in graph)",
        answer=user_answer,
    ).strip()

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You must output ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 200,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # -----------------------------------------------------
    # Groq API CALL
    # -----------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)

        data = resp.json()
        logger.info("Groq eval response: %s", data)

        if "error" in data:
            return _fallback(user_answer, f"Groq error: {data['error']}")

        content = data["choices"][0]["message"]["content"]
        result = safe_json(content)

        # Ensure technical depth is zero for non-technical stages
        if stage in ["intro", "hr", "behavioral", "managerial", "wrap-up"]:
            result["technical_depth"] = 0

        # Fill missing fields safely
        return {
            "clarity": int(result.get("clarity", 5)),
            "confidence": int(result.get("confidence", 5)),
            "technical_depth": int(result.get("technical_depth", 0)),
            "summary": result.get("summary", "(No summary provided)"),
        }

    except Exception as e:
        logger.exception("Evaluation failed:")
        return _fallback(user_answer, str(e))


# ---------------------------------------------------------
# FALLBACK — NEVER let the pipeline break
# ---------------------------------------------------------
def _fallback(answer: str, reason: str):
    """Fallback evaluation if LLM fails."""
    return {
        "clarity": 5,
        "confidence": 5,
        "technical_depth": 0,
        "summary": f"(Fallback due to: {reason}) Answer: {answer[:80]}...",
    }


# ---------------------------------------------------------
# Summary aggregator (used for final reports)
# ---------------------------------------------------------
def summarize_scores(evaluations: list[dict]) -> dict:
    if not evaluations:
        return {
            "clarity": 0,
            "confidence": 0,
            "technical_depth": 0,
            "overall": "No Data",
        }

    avg = {
        "clarity": sum(ev.get("clarity", 0) for ev in evaluations) / len(evaluations),
        "confidence": sum(ev.get("confidence", 0) for ev in evaluations) / len(evaluations),
        "technical_depth": sum(ev.get("technical_depth", 0) for ev in evaluations) / len(evaluations),
    }

    overall = sum(avg.values()) / len(avg)

    band = (
        "Strong Fit" if overall >= 8.5
        else "Average Fit" if overall >= 7
        else "Weak Fit" if overall >= 5
        else "No Hire"
    )

    # FIXED: cleaner version
    rounded = {k: round(v, 2) for k, v in avg.items()}
    rounded["overall"] = band
    return rounded