# apps/api/app.py
from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
load_dotenv() 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

# ✨ Your existing routers
#from apps.api.routers.auth import router as auth_router
from apps.api.routers.evaluation import router as evaluation_router
#from apps.api.routers.sessions import router as sessions_router

# ✅ NEW: CV router (add this file at apps/api/routers/cv.py as we discussed)
from apps.api.routers.cv import router as cv_router

from apps.api.routers.upload import router as upload_router  

# If you have a settings module, great; otherwise hardcode minimal defaults
try:
    from apps.api.settings import settings  # optional convenience
    APP_NAME = settings.project_name
    API_PREFIX = settings.api_v1_str
    CORS_ORIGINS = settings.backend_cors_origins
except Exception:
    APP_NAME = "Interview Coach API"
    API_PREFIX = "/"
    CORS_ORIGINS = ["*"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting %s", APP_NAME)
    yield
    logger.info("🛑 Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Middleware ──────────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health ──────────────────────────────────────────────────────────────────
    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    # ── Routers (versioned inside each router via prefix) ───────────────────────
    #app.include_router(auth_router)         # usually has prefix="/v1/auth"
    app.include_router(evaluation_router)   # e.g., "/v1/evaluation" or similar
    #app.include_router(sessions_router)     # e.g., "/v1/sessions"
    app.include_router(cv_router)           # NEW: "/v1/cv"

    app.include_router(upload_router) 

    return app


app = create_app()
