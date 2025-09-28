from fastapi import FastAPI
from apps.api.interview_routes import router as interview_router
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

print("🔑 GROQ_API_KEY loaded?", os.getenv("GROQ_API_KEY") is not None)
print("🤖 LLM_MODEL:", os.getenv("LLM_MODEL"))


app = FastAPI(title="AI Interview Backend")

# Register interview routes
app.include_router(interview_router, prefix="/v1/interview", tags=["Interview"])
