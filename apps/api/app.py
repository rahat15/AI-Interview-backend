from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging
import os

# Load env
load_dotenv()

# Routers
from apps.api.routers.cv import router as cv_router
from apps.api.routers.upload import router as upload_router
from apps.api.routers.evaluation import router as evaluation_router
from apps.api.routers.sessions import router as sessions_router
from apps.api.routers.overview import router as overview_router
from apps.api.routers.jd import router as jd_router
from apps.api.routers.audio import router as audio_router
from apps.api.routers.resume import router as resume_router
from apps.api.routers.interview_v2 import router as interview_v2_router
from apps.api.interview_routes import router as interview_router
from apps.api.routers.optimized_interview_routes import router as optimized_interview_router

# DB
from core.db import connect_to_mongo, close_mongo_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")
if ROOT_PATH and not ROOT_PATH.startswith("/"):
    ROOT_PATH = "/" + ROOT_PATH

print("🌐 ROOT_PATH:", ROOT_PATH or "(none)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting up...")
    try:
        await connect_to_mongo()
        logger.info("✅ Mongo connected")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}")
        logger.info("⚠️  Continuing without MongoDB - V2 endpoints will work (in-memory sessions)")
    yield
    logger.info("🛑 Shutting down...")
    try:
        await close_mongo_connection()
        logger.info("✅ Mongo disconnected")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB disconnect error: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Interview Coach API",
        version="1.0.0",
        root_path=ROOT_PATH,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        swagger_ui_parameters={
            # 🔑 THIS IS THE CRITICAL FIX
            "url": f"{ROOT_PATH}/openapi.json" if ROOT_PATH else "/openapi.json"
        },
        lifespan=lifespan,
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

    # Health
    @app.get("/healthz", tags=["Health"])
    async def health():
        return {
            "status": "ok",
            "message": "AI Interview Coach API is running",
            "version": "1.0.0",
        }

    # Routers
    app.include_router(overview_router, tags=["Overview"])
    app.include_router(cv_router, tags=["CV"])
    app.include_router(upload_router, prefix="/v1/upload", tags=["Upload"])
    app.include_router(evaluation_router, prefix="/v1/evaluation", tags=["Evaluation"])
    app.include_router(sessions_router, prefix="/v1/sessions", tags=["Sessions"])
    app.include_router(jd_router, prefix="/v1/jd", tags=["JD"])
    app.include_router(audio_router, prefix="/v1/audio", tags=["Audio"])
    app.include_router(resume_router, prefix="/v1", tags=["Resume"])
    app.include_router(interview_router, prefix="/v1/interview", tags=["Interview"])
    
    # V2 Interview - Gemini-powered
    app.include_router(interview_v2_router, tags=["Interview V2"])
    
    # V2 Optimized - LangGraph with caching & streaming
    app.include_router(optimized_interview_router, prefix="/interview", tags=["Interview V2 Optimized"])

    # Legacy
    app.include_router(interview_router, prefix="/interview", tags=["Interview (Legacy)"])

    return app


app = create_app()
