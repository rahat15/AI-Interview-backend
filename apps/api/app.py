from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

# from dotenv import load_dotenv
# load_dotenv()

# Import routers
from apps.api.routers.cv import router as cv_router
from apps.api.routers.upload import router as upload_router
from apps.api.routers.evaluation import router as evaluation_router
from apps.api.routers.sessions import router as sessions_router
from apps.api.routers.overview import router as overview_router
from apps.api.routers.jd import router as jd_router
# from apps.api.routers.audio import router as audio_router
from apps.api.routers.resume import router as resume_router
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
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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

    # ✅ Health check
    @app.get("/healthz", tags=["Health"])
    async def healthz():
        return {"status": "ok"}

    # Routers
    app.include_router(overview_router, tags=["API Overview"])
    app.include_router(cv_router, tags=["CV Evaluation"])
    app.include_router(upload_router, tags=["File Upload & Processing"])
    app.include_router(evaluation_router, tags=["Direct Evaluation"])
    app.include_router(sessions_router, tags=["Session Management"])
    app.include_router(jd_router, prefix="/v1/jd", tags=["Job Description"])
    app.include_router(resume_router, tags=["Resume Upload"])
    app.include_router(interview_router, prefix="/api/interview", tags=["Interview"])
    app.include_router(interview_router, tags=["Interview (Legacy)"])

    return app   # ✅ RETURN AT THE VERY END


app = create_app()