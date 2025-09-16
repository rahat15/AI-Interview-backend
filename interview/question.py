import httpx
import os

# Get Groq API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("LLM_MODEL")  # or change based on preference

async def generate_question(state, stage, followup=False):
    prompt = f"""
    You are an interviewer for {state['config']['role_title']} at {state['config']['company_name']}
    in the {state['config']['industry']} industry.

    Current stage: {stage}
    Job Description: {state['jd']}
    CV: {state['cv']}
    Previous Q&A: {state['history']}

    {'Ask a follow-up question to clarify the last answer.' if followup else 'Ask the next question.'}
    """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
