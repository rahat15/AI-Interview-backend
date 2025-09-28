import httpx
import os
import json

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL")

async def evaluate_answer(user_answer, jd, cv):
    prompt = f"""
    Evaluate this interview answer.

    Answer: {user_answer}
    Job Description: {jd}
    CV: {cv}

    Rubric:
    - Technical Depth (0-10)
    - Relevance to JD (0-10)
    - Communication (0-10)
    - Behavioral/Soft Skills (0-10)

    Provide JSON strictly:
    {{
      "technical_depth": int,
      "relevance": int,
      "communication": int,
      "behavioral": int,
      "feedback": "short narrative feedback"
    }}
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 300
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
        data = resp.json()
        try:
            return json.loads(data["choices"][0]["message"]["content"])
        except Exception:
            return {"feedback": "Error parsing evaluation."}
def summarize_scores(evaluations: list[dict]) -> dict:
    """Aggregate evaluations into a final score report"""
    if not evaluations:
        return {
            "technical_depth": 0,
            "relevance": 0,
            "communication": 0,
            "behavioral": 0,
            "overall": "No Data"
        }

    totals = {"technical_depth": 0, "relevance": 0, "communication": 0, "behavioral": 0}
    count = len(evaluations)

    for ev in evaluations:
        totals["technical_depth"] += ev.get("technical_depth", 0)
        totals["relevance"] += ev.get("relevance", 0)
        totals["communication"] += ev.get("communication", 0)
        totals["behavioral"] += ev.get("behavioral", 0)

    averages = {k: round(v / count, 2) for k, v in totals.items()}

    overall_score = sum(averages.values()) / len(averages)
    if overall_score >= 8.5:
        overall = "Strong Hire"
    elif overall_score >= 7:
        overall = "Hire"
    elif overall_score >= 5:
        overall = "Weak Hire"
    else:
        overall = "No Hire"

    return {**averages, "overall": overall}
