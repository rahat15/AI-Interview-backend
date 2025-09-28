import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # load .env if not already loaded

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")

if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY not set in environment!")

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}
payload = {
    "model": GROQ_MODEL,
    "messages": [{"role": "user", "content": "Hello Groq! Just say 'pong' if you can hear me."}],
    "max_tokens": 20,
}

print("🔄 Sending test request to Groq...")
resp = httpx.post(url, headers=headers, json=payload, timeout=30)

print("Status:", resp.status_code)
print("Response:", resp.json())
