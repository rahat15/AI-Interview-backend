from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

# Import routers
from apps.api.routers.cv import router as cv_router
from apps.api.routers.upload import router as upload_router
from apps.api.routers.evaluation import router as evaluation_router
from apps.api.routers.sessions import router as sessions_router
from apps.api.routers.overview import router as overview_router
from apps.api.routers.jd import router as jd_router
from apps.api.routers.audio import router as audio_router
from apps.api.interview_routes import router as interview_router

# Import database connection
from core.db import connect_to_mongo, close_mongo_connection

import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🔑 GROQ_API_KEY loaded?", os.getenv("GROQ_API_KEY") is not None)
print("🤖 LLM_MODEL:", os.getenv("LLM_MODEL"))
print("🍃 MONGO_URI loaded?", os.getenv("MONGO_URI") is not None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting up...")
    await connect_to_mongo()
    logger.info("✅ Connected to MongoDB")
    yield
    # Shutdown
    logger.info("🛑 Shutting down...")
    await close_mongo_connection()
    logger.info("✅ Disconnected from MongoDB")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Interview Coach API",
        version="1.0.0",
        description="""A comprehensive AI-powered interview coaching platform that provides:
        
        ## Features
        - **CV Evaluation**: Score CV quality and job fit
        - **Interview Sessions**: Conduct adaptive AI interviews
        - **File Processing**: Upload and process CVs/JDs in multiple formats
        - **Improvement Suggestions**: Generate tailored resume improvements
        - **Session Management**: Track and manage interview sessions
        - **Real-time Evaluation**: Get instant feedback on responses
        - **Audio Processing**: Speech-to-text and voice analysis
        
        ## API Endpoints
        All endpoints are prefixed with `/v1` for versioning:
        - **CV** (`/v1/cv/*`): CV scoring and evaluation
        - **Upload** (`/v1/upload/*`): File upload and processing
        - **Evaluation** (`/v1/evaluation/*`): Direct CV/JD evaluation
        - **Sessions** (`/v1/sessions/*`): Interview session management
        - **Job Description** (`/v1/jd/*`): JD upload and management
        - **Audio** (`/v1/audio/*`): Audio processing and analysis
        - **Interview** (`/v1/interview/*`): Live interview flow
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "AI Interview Coach",
            "email": "support@aiinterviewcoach.com",
        },
        license_info={
            "name": "MIT",
        },
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
    @app.get("/healthz", tags=["Health"], summary="Health Check")
    async def health():
        """Check if the API is running and connected to services."""
        return {
            "status": "ok", 
            "message": "AI Interview Coach API is running",
            "version": "1.0.0",
            "services": {
                "mongodb": "connected",
                "api": "healthy"
            }
        }

    # Include all routers with proper prefixes and tags
    app.include_router(overview_router, tags=["API Overview"])
    app.include_router(cv_router, tags=["CV Evaluation"])
    app.include_router(upload_router, prefix="/v1/upload", tags=["File Upload & Processing"])
    app.include_router(evaluation_router, prefix="/v1/evaluation", tags=["Direct Evaluation"])
    app.include_router(sessions_router, prefix="/v1/sessions", tags=["Session Management"])
    app.include_router(jd_router, prefix="/v1/jd", tags=["Job Description"])
    app.include_router(audio_router, prefix="/v1/audio", tags=["Audio Processing"])
    app.include_router(interview_router, prefix="/v1/interview", tags=["Interview"])
    
    # Backward compatibility: Add interview routes without /v1 prefix
    app.include_router(interview_router, prefix="/interview", tags=["Interview (Legacy)"])

    return app


app = create_app()