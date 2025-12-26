from fastapi import APIRouter
from typing import Dict, List, Any

router = APIRouter(prefix="/api", tags=["API Overview"])

@router.get("/", summary="API Overview")
async def api_overview():
    """
    Get a comprehensive overview of all available API endpoints.
    """
    return {
        "message": "Welcome to AI Interview Coach API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "cv_evaluation": {
                "description": "CV scoring and evaluation",
                "endpoints": [
                    "POST /api/v1/cv/score - Score CV quality only",
                    "POST /api/v1/cv/fit-index - Score CV + JD match",
                    "POST /api/v1/cv/improvement - Generate CV improvements"
                ]
            },
            "file_processing": {
                "description": "File upload and processing",
                "endpoints": [
                    "POST /api/upload/cv_evaluate - Upload CV for evaluation",
                    "POST /api/upload/cv_improvement - Upload CV for improvement"
                ]
            },
            "direct_evaluation": {
                "description": "Direct text evaluation",
                "endpoints": [
                    "POST /api/evaluation/cv - Evaluate CV vs JD (JSON input)"
                ]
            },
            "session_management": {
                "description": "Interview session management",
                "endpoints": [
                    "POST /api/sessions/ - Create new session",
                    "GET /api/sessions/ - List all sessions",
                    "GET /api/sessions/{id} - Get session details",
                    "GET /api/sessions/{id}/next-question - Get next question",
                    "POST /api/sessions/{id}/answer - Submit answer",
                    "GET /api/sessions/{id}/report - Get session report",
                    "DELETE /api/sessions/{id} - Delete session"
                ]
            },
            "artifact_management": {
                "description": "File artifact management",
                "endpoints": [
                    "POST /api/uploads/cv - Upload CV file",
                    "POST /api/uploads/jd - Upload JD file",
                    "GET /api/uploads/{id} - Get artifact details",
                    "DELETE /api/uploads/{id} - Delete artifact"
                ]
            },
            "live_interview": {
                "description": "Live interview flow management",
                "endpoints": [
                    "POST /api/interview/start - Start interview session",
                    "POST /api/interview/answer - Submit interview answer",
                    "GET /api/interview/state/{user_id}/{session_id} - Get interview state",
                    "GET /api/interview/sessions/{user_id} - Get user sessions",
                    "GET /api/interview/report/{user_id}/{session_id} - Get interview report"
                ]
            },
            "health": {
                "description": "System health and status",
                "endpoints": [
                    "GET /healthz - Health check"
                ]
            }
        },
        "supported_file_formats": [
            "PDF (.pdf)",
            "Word Documents (.docx, .doc)",
            "Text Files (.txt, .md)",
            "Rich Text Format (.rtf)",
            "HTML (.html, .htm)",
            "OpenDocument Text (.odt)",
            "Images with OCR (.png, .jpg, .jpeg, .tif, .tiff)"
        ],
        "features": [
            "CV Quality Scoring",
            "Job Description Matching",
            "AI-Powered Interview Sessions",
            "Real-time Evaluation",
            "Improvement Suggestions",
            "Multi-format File Processing",
            "Session Management",
            "Comprehensive Reporting"
        ]
    }