from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from dotenv import load_dotenv
load_dotenv()

# Import routers
from apps.api.routers.cv import router as cv_router
from apps.api.routers.upload import router as upload_router
from apps.api.interview_routes import router as interview_router

import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🔑 GROQ_API_KEY loaded?", os.getenv("GROQ_API_KEY") is not None)
print("🤖 LLM_MODEL:", os.getenv("LLM_MODEL"))


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Interview Backend",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/healthz")
    async def health():
        return {"status": "ok"}

    # Routers
    app.include_router(cv_router, prefix="/v1", tags=["CV"])
    app.include_router(upload_router, prefix="/v1", tags=["Upload"])
    app.include_router(interview_router, prefix="/v1", tags=["Interview"])

    return app


app = create_app()
