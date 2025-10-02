import httpx
import os
import json
import logging
from ..prompts import BASE_EVALUATION_PROMPT

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")


async def evaluate_answer(stage: str, question: str, user_answer: str, jd: str, cv: str) -> dict:
    """
    Evaluate a candidate's answer using Groq API.
    Returns JSON with clarity, confidence, technical_depth, and summary.
    """

    # Build prompt from central template
    prompt = BASE_EVALUATION_PROMPT.format(
        stage=stage,
        question=question,
        answer=user_answer
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt.strip()}],
        "temperature": 0.2,  # keep eval consistent
        "max_tokens": 250,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            data = resp.json()

            logging.info("Groq eval response: %s", data)

            if "choices" not in data:
                error_msg = data.get("error", {}).get("message", "Unknown error from Groq")
                return _fallback_eval(stage, user_answer, f"Groq error: {error_msg}")

            raw_eval = data["choices"][0]["message"]["content"].strip()

            try:
                evaluation = json.loads(raw_eval)
                # Force technical_depth=0 for non-technical stages
                if stage in ["intro", "hr", "behavioral", "managerial", "wrap-up"]:
                    evaluation["technical_depth"] = 0
                return evaluation
            except Exception as e:
                logging.warning("Failed to parse JSON eval. Raw: %s", raw_eval)
                return _fallback_eval(stage, user_answer, f"Parse error: {e}")

    except Exception as e:
        logging.exception("Exception in evaluate_answer")
        return _fallback_eval(stage, user_answer, str(e))


def _fallback_eval(stage: str, answer: str, error: str) -> dict:
    """
    Fallback evaluation if Groq fails or JSON parsing breaks.
    """
    return {
        "technical_depth": 0 if stage in ["intro", "hr", "behavioral", "managerial", "wrap-up"] else 5,
        "clarity": 5,
        "confidence": 5,
        "summary": f"(Fallback eval due to {error}). Candidate answer snippet: {answer[:100]}..."
    }


def summarize_scores(evaluations: list[dict]) -> dict:
    """
    Aggregate all evaluations into a final report with banding.
    """
    if not evaluations:
        return {
            "technical_depth": 0,
            "clarity": 0,
            "confidence": 0,
            "overall": "No Data"
        }

    totals = {"technical_depth": 0, "clarity": 0, "confidence": 0}
    count = len(evaluations)

    # Sum up all scores
    for ev in evaluations:
        totals["technical_depth"] += ev.get("technical_depth", 0)
        totals["clarity"] += ev.get("clarity", 0)
        totals["confidence"] += ev.get("confidence", 0)

    # Compute averages
    averages = {k: round(v / count, 2) for k, v in totals.items()}

    # Compute overall average
    overall_score = sum(averages.values()) / len(averages)

    # Assign band
    if overall_score >= 8.5:
        overall = "Strong Fit"
    elif overall_score >= 7:
        overall = "Average Fit"
    elif overall_score >= 5:
        overall = "Weak Fit"
    else:
        overall = "No Hire"

    return {
        **averages,
        "overall": overall
    }
