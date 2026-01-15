from fastapi import APIRouter, HTTPException, status, Form
from typing import List, Optional
from datetime import datetime
import httpx
import uuid

from core.models import Session as SessionModel, Resume, Answer
from core.schemas import (
    SessionCreate,
    Session as SessionSchema,
    NextQuestionResponse,
    AnswerCreate,
    Report as ReportSchema,
)

router = APIRouter()

# Base URL for fetching resume data
RESUME_BASE_URL = "http://localhost:3000"

# --------- Helper Functions ---------

async def fetch_resume_from_db(resume_id: str) -> Optional[dict]:
    """Fetch resume from MongoDB by ID"""
    try:
        from bson import ObjectId
        from core.db import get_database
        
        db = await get_database()
        
        # Try different query approaches
        resume_doc = None
        
        # Try as ObjectId first
        try:
            if ObjectId.is_valid(resume_id):
                resume_doc = await db.resumes.find_one({"_id": ObjectId(resume_id)})
        except:
            pass
        
        # Try as string ID
        if not resume_doc:
            resume_doc = await db.resumes.find_one({"_id": resume_id})
        
        # Try as user field (in case it's a user ID)
        if not resume_doc:
            resume_doc = await db.resumes.find_one({"user": resume_id})
        
        if resume_doc:
            return {
                "id": str(resume_doc.get("_id")),
                "filename": resume_doc.get("filename", ""),
                "path": resume_doc.get("path", ""),
                "stats": resume_doc.get("stats", {}),
                "user": resume_doc.get("user", ""),
                "created_at": resume_doc.get("createdAt", resume_doc.get("created_at"))
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching resume: {e}")
        return None

async def fetch_resume_content(file_path: str) -> str:
    """Fetch resume content from file path via HTTP"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RESUME_BASE_URL}/{file_path}")
            if response.status_code == 200:
                return response.text
            return ""
    except Exception as e:
        print(f"Error fetching resume content: {e}")
        return ""

# --------- Endpoints ---------

@router.post("/", response_model=SessionSchema)
async def create_session(session_in: SessionCreate):
    """Create a new interview session with MongoDB integration."""
    try:
        # Create new session
        session_data = {
            "id": str(uuid.uuid4()),
            "user_id": "default_user",  # You can get this from auth
            "role": session_in.role,
            "industry": session_in.industry,
            "company": session_in.company,
            "status": "active",
            "current_question_index": 0,
            "total_questions": 10,  # Default value
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "plan_json": None
        }
        
        # Handle CV file ID - fetch from Resume collection
        if session_in.cv_file_id:
            resume_data = await fetch_resume_from_db(session_in.cv_file_id)
            if resume_data:
                session_data["cv_file_id"] = session_in.cv_file_id
                # Optionally fetch the actual content
                cv_content = await fetch_resume_content(resume_data["path"])
                if cv_content:
                    session_data["cv_content"] = cv_content
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Resume with ID {session_in.cv_file_id} not found"
                )
        
        # Handle JD - either from file or text
        if session_in.jd_file_id:
            session_data["jd_file_id"] = session_in.jd_file_id
        elif session_in.jd_text:
            # Store JD text in plan_json
            session_data["plan_json"] = {"jd_text": session_in.jd_text}
        
        # Create session in MongoDB
        session = SessionModel(**session_data)
        await session.insert()
        
        return SessionSchema(
            id=session.id,
            user_id=session.user_id,
            role=session.role,
            industry=session.industry,
            company=session.company,
            status=session.status,
            plan_json=session.plan_json,
            cv_file_id=session.cv_file_id,
            jd_file_id=session.jd_file_id,
            current_question_index=session.current_question_index,
            total_questions=session.total_questions,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionSchema)
async def get_session(session_id: str):
    """Get session by ID"""
    try:
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionSchema(
            id=session.id,
            user_id=session.user_id,
            role=session.role,
            industry=session.industry,
            company=session.company,
            status=session.status,
            plan_json=session.plan_json,
            cv_file_id=session.cv_file_id,
            jd_file_id=session.jd_file_id,
            current_question_index=session.current_question_index,
            total_questions=session.total_questions,
            created_at=session.created_at,
            updated_at=session.updated_at,
            completed_at=session.completed_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@router.get("/", response_model=List[SessionSchema])
async def list_sessions():
    """List all sessions"""
    try:
        sessions = await SessionModel.find_all().to_list()
        return [
            SessionSchema(
                id=session.id,
                user_id=session.user_id,
                role=session.role,
                industry=session.industry,
                company=session.company,
                status=session.status,
                plan_json=session.plan_json,
                cv_file_id=session.cv_file_id,
                jd_file_id=session.jd_file_id,
                current_question_index=session.current_question_index,
                total_questions=session.total_questions,
                created_at=session.created_at,
                updated_at=session.updated_at,
                completed_at=session.completed_at
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.get("/{session_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(session_id: str):
    """Get next question for session"""
    try:
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Mock questions for now
        questions = [
            {"text": "Tell me about yourself", "competency": "intro", "difficulty": "easy"},
            {"text": "What are your strengths?", "competency": "behavioral", "difficulty": "medium"},
            {"text": "Describe a challenging project", "competency": "technical", "difficulty": "hard"},
            {"text": "Why do you want this role?", "competency": "motivation", "difficulty": "medium"},
        ]
        
        idx = session.current_question_index
        if idx >= len(questions):
            session.status = "completed"
            await session.save()
            raise HTTPException(status_code=404, detail="No more questions - session completed")

        question = questions[idx]
        return NextQuestionResponse(
            question_id=str(uuid.uuid4()),
            text=question["text"],
            competency=question["competency"],
            difficulty=question["difficulty"],
            meta={}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting next question: {str(e)}")


@router.post("/{session_id}/answer")
async def submit_answer(session_id: str, answer_in: AnswerCreate):
    """Submit answer for current question"""
    try:
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.current_question_index >= session.total_questions:
            raise HTTPException(status_code=400, detail="No pending question to answer")

        # Update session progress
        session.current_question_index += 1
        session.updated_at = datetime.utcnow()
        
        if session.current_question_index >= session.total_questions:
            session.status = "completed"
            session.completed_at = datetime.utcnow()
        
        await session.save()

        return {
            "message": "Answer submitted successfully",
            "answer_id": str(uuid.uuid4()),
            "next_question_index": session.current_question_index,
            "session_completed": session.status == "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")




@router.get("/{session_id}/report", response_model=ReportSchema)
async def get_session_report(session_id: str):
    """Get session report"""
    try:
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Generate mock report
        return ReportSchema(
            id=str(uuid.uuid4()),
            session_id=session_id,
            report_json={
                "summary": "Great performance overall",
                "overall_score": 85.0,
                "competency_breakdown": {
                    "technical": 4.2,
                    "behavioral": 4.0,
                    "communication": 4.1
                }
            },
            summary="Great performance overall with strong technical skills",
            overall_score=85.0,
            strengths=["Technical expertise", "Clear communication", "Problem-solving"],
            areas_for_improvement=["Leadership examples", "More specific metrics"],
            recommendations=["Practice STAR method", "Prepare leadership stories"],
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete session"""
    try:
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        await session.delete()
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


# Additional endpoint to handle JD text directly
@router.post("/{session_id}/jd-text")
async def add_jd_text(session_id: str, jd_data: dict):
    """Add JD text to existing session"""
    try:
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Store JD text in session metadata
        if not session.plan_json:
            session.plan_json = {}
        session.plan_json["jd_text"] = jd_data.get("jd_text", "")
        session.updated_at = datetime.utcnow()
        
        await session.save()
        
        return {"message": "JD text added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding JD text: {str(e)}")

@router.get("/resume/{resume_id}")
async def get_resume_details(resume_id: str):
    """Get resume details from MongoDB"""
    try:
        resume_data = await fetch_resume_from_db(resume_id)
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return resume_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching resume: {str(e)}")

@router.get("/debug/resumes")
async def list_all_resumes():
    """Debug endpoint to list all resumes in the collection"""
    try:
        from core.db import get_database
        db = await get_database()
        
        # Get all resumes from the collection
        resumes = await db.resumes.find({}).to_list(length=100)
        
        return {
            "total_count": len(resumes),
            "resumes": [
                {
                    "id": str(resume.get("_id", resume.get("id", ""))),
                    "filename": resume.get("filename", ""),
                    "user": resume.get("user", ""),
                    "created_at": resume.get("createdAt", resume.get("created_at", "")),
                    "has_stats": "stats" in resume
                }
                for resume in resumes
            ]
        }
    except Exception as e:
        return {"error": f"Failed to fetch resumes: {str(e)}"}

@router.get("/debug/resume/{resume_id}")
async def debug_get_resume(resume_id: str):
    """Debug endpoint to get specific resume with detailed info"""
    try:
        from core.db import get_database
        db = await get_database()
        
        # Try multiple query methods
        queries = [
            {"_id": resume_id},
            {"id": resume_id},
            {"user": resume_id}  # In case resume_id is actually user_id
        ]
        
        results = {}
        for i, query in enumerate(queries):
            try:
                resume = await db.resumes.find_one(query)
                results[f"query_{i}_{list(query.keys())[0]}"] = resume is not None
                if resume:
                    results[f"query_{i}_data"] = {
                        "id": str(resume.get("_id", "")),
                        "filename": resume.get("filename", ""),
                        "path": resume.get("path", ""),
                        "user": resume.get("user", ""),
                        "has_stats": "stats" in resume
                    }
            except Exception as e:
                results[f"query_{i}_error"] = str(e)
        
        return {
            "resume_id_searched": resume_id,
            "query_results": results
        }
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}