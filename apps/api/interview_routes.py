# apps/api/routers/interview_routes.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from interview.session_manager import interview_manager
import tempfile
import os

# Helper functions for fetching content
async def fetch_resume_content(resume_id: str) -> Optional[str]:
    """Fetch resume content from MongoDB"""
    try:
        from bson import ObjectId
        from core.db import get_database
        
        db = await get_database()
        print(f"🔍 Searching for resume with ID: {resume_id}")
        
        # Try to find resume
        resume_doc = None
        if ObjectId.is_valid(resume_id):
            resume_doc = await db.resumes.find_one({"_id": ObjectId(resume_id)})
            print(f"🔍 ObjectId query result: {resume_doc is not None}")
        
        if not resume_doc:
            resume_doc = await db.resumes.find_one({"_id": resume_id})
            print(f"🔍 String ID query result: {resume_doc is not None}")
        
        if not resume_doc:
            resume_doc = await db.resumes.find_one({"user": resume_id})
            print(f"🔍 User ID query result: {resume_doc is not None}")
        
        if resume_doc:
            print(f"🔍 Found resume: {resume_doc.get('filename', 'Unknown')}")
            
            # Try to fetch file content from path
            file_path = resume_doc.get("path", "")
            if file_path:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"http://localhost:3000/{file_path}")
                        if response.status_code == 200:
                            content = response.text
                            print(f"✅ Fetched file content: {len(content)} chars")
                            return content
                except Exception as e:
                    print(f"⚠️ Failed to fetch file content: {e}")
            
            # Fallback to stats or basic info
            stats = resume_doc.get("stats", {})
            if stats:
                # Extract meaningful content from stats
                cv_quality = stats.get("cv_quality", {})
                subscores = cv_quality.get("subscores", [])
                
                content_parts = [f"Resume: {resume_doc.get('filename', 'Unknown')}"]
                
                for subscore in subscores:
                    evidence = subscore.get("evidence", [])
                    if evidence:
                        content_parts.extend(evidence)
                
                content = "\n".join(content_parts)
                print(f"✅ Generated content from stats: {len(content)} chars")
                return content
            
            # Final fallback
            return f"Resume: {resume_doc.get('filename', 'Unknown')} (Content not available)"
        
        print(f"❌ No resume found with ID: {resume_id}")
        return None
    except Exception as e:
        print(f"❌ Error fetching resume content: {e}")
        return None

async def fetch_jd_content(jd_id: str) -> Optional[str]:
    """Fetch JD content from MongoDB"""
    try:
        from bson import ObjectId
        from core.db import get_database
        
        db = await get_database()
        
        # Try to find JD
        jd_doc = None
        if ObjectId.is_valid(jd_id):
            jd_doc = await db.jobdescriptions.find_one({"_id": ObjectId(jd_id)})
        
        if not jd_doc:
            jd_doc = await db.jobdescriptions.find_one({"_id": jd_id})
        
        if jd_doc:
            # Return text content if available
            text_content = jd_doc.get("text", "")
            if text_content:
                return text_content
            
            # Try to fetch file content from path
            file_path = jd_doc.get("path", "")
            if file_path:
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"http://localhost:3000/{file_path}")
                        if response.status_code == 200:
                            return response.text
                except:
                    pass
            
            # Fallback to filename
            return f"Job Description: {jd_doc.get('filename', 'Unknown')}"
        
        return None
    except Exception as e:
        print(f"Error fetching JD content: {e}")
        return None

# No prefix here; prefix is added in app.include_router
router = APIRouter()

# ---------------------------
# Request / Response Schemas
# ---------------------------

class StartSessionRequest(BaseModel):
    user_id: str
    session_id: str
    role_title: str
    company_name: str
    industry: str
    jd: Optional[str] = ""
    cv: Optional[str] = ""
    jd_id: Optional[str] = None  # JD file ID
    cv_id: Optional[str] = None  # Resume file ID
    round_type: Optional[str] = "full"


class StartSessionResponse(BaseModel):
    session_id: str
    user_id: str
    first_question: str
    state: Dict[str, Any]
    cv_content: Optional[str] = None  # Include CV content in response
    jd_content: Optional[str] = None  # Include JD content in response



class AnswerResponse(BaseModel):
    evaluation: Optional[Dict[str, Any]]
    next_question: Optional[str]
    state: Dict[str, Any]
    video_analysis: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    session_id: str
    user_id: str
    role: str
    company: str
    industry: str
    avg_scores: Dict[str, Any]
    history: List[Dict[str, Any]]

# ---------------------------
# Routes
# ---------------------------

@router.post("/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest):
    """
    Start a new interview session.
    Creates a session, initializes state, and returns the first question.
    Supports both direct text and file IDs for CV/JD.
    """
    try:
        # Fetch CV content if cv_id is provided
        cv_content = req.cv
        if req.cv_id:
            cv_data = await fetch_resume_content(req.cv_id)
            if cv_data:
                cv_content = cv_data
                print(f"✅ Fetched CV content: {cv_content[:100]}...")
            else:
                print(f"❌ Resume with ID {req.cv_id} not found")
                raise HTTPException(status_code=404, detail=f"Resume with ID {req.cv_id} not found")
        
        # Fetch JD content if jd_id is provided
        jd_content = req.jd
        if req.jd_id:
            jd_data = await fetch_jd_content(req.jd_id)
            if jd_data:
                jd_content = jd_data
                print(f"✅ Fetched JD content: {jd_content[:100]}...")
            else:
                print(f"❌ JD with ID {req.jd_id} not found")
                raise HTTPException(status_code=404, detail=f"JD with ID {req.jd_id} not found")
        
        print(f"🔍 Final CV content length: {len(cv_content)}")
        print(f"🔍 Final JD content length: {len(jd_content)}")
        
        state = interview_manager.create_session(
            user_id=req.user_id,
            session_id=req.session_id,
            role_title=req.role_title,
            company_name=req.company_name,
            industry=req.industry,
            jd=jd_content,
            cv=cv_content,
            round_type=req.round_type,
        )

        # Advance graph until first question
        result = await interview_manager.step(req.user_id, req.session_id)

        history = result.get("history", [])
        if not history:
            raise RuntimeError("No question generated by graph")

        first_question = history[-1]["question"]

        return {
            "user_id": req.user_id,
            "session_id": req.session_id,
            "first_question": first_question,
            "state": result,
            "cv_content": cv_content if cv_content else None,
            "jd_content": jd_content if jd_content else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    user_id: str = Form(...),
    session_id: str = Form(...),
    audio_file: UploadFile = File(None),
    video_file: UploadFile = File(None)
):
    """
    Submit audio/video answer to the current question.
    Supports:
    - Audio only: Speech-to-text + voice analysis
    - Video only: Extract audio + video behavior analysis  
    - Both: Complete analysis with cheating detection
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 RECEIVED REQUEST - user_id: {user_id}, session_id: {session_id}")
        print(f"📁 audio_file: {audio_file.filename if audio_file else 'None'} (exists: {audio_file is not None})")
        print(f"📁 video_file: {video_file.filename if video_file else 'None'} (exists: {video_file is not None})")
        print(f"{'='*60}\n")
        # Validate session exists first
        session_state = interview_manager.get_state(user_id, session_id)
        if not session_state:
            raise HTTPException(
                status_code=404, 
                detail={"error": f"Session not found for user_id: {user_id}, session_id: {session_id}"}
            )
        
        if not audio_file and not video_file:
            raise HTTPException(status_code=400, detail={"error": "Either audio or video file is required"})
        
        answer_text = ""
        video_analysis = None
        video_data = None
        
        # Process video if provided
        if video_file:
            from interview.video_analyzer import video_analyzer
            video_data = await video_file.read()
            video_analysis = video_analyzer.analyze_video(video_data)
            print(f"🎥 VIDEO ANALYSIS - Cheating risk: {video_analysis['cheating_detection']['risk_level']}")
        
        # Process audio - if audio_file is empty, extract from video
        audio_data = None
        if audio_file:
            audio_data = await audio_file.read()
            print(f"🔊 AUDIO FILE - Name: {audio_file.filename}, Size: {len(audio_data)} bytes")
            
            if len(audio_data) == 0:
                print("⚠️ WARNING: Audio file is EMPTY (0 bytes)")
                audio_data = None
        
        # If no valid audio but video exists, extract audio from video
        if not audio_data and video_file and video_data:
            print("🎬 Extracting audio from video file...")
            try:
                import tempfile
                import subprocess
                
                # Save video temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_tmp:
                    video_tmp.write(video_data)
                    video_path = video_tmp.name
                
                # Extract audio using ffmpeg
                audio_path = video_path.replace('.mp4', '.wav')
                result = subprocess.run(
                    ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path, '-y'],
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0 and os.path.exists(audio_path):
                    with open(audio_path, 'rb') as f:
                        audio_data = f.read()
                    print(f"✅ Extracted audio from video: {len(audio_data)} bytes")
                    os.remove(audio_path)
                else:
                    print(f"❌ Failed to extract audio from video: {result.stderr.decode()}")
                
                os.remove(video_path)
            except Exception as e:
                print(f"❌ Audio extraction error: {e}")
        
        # Transcribe audio if available
        if audio_data and len(audio_data) > 100:
            from interview.speech_to_text import speech_converter
            answer_text = speech_converter.convert_audio_to_text(audio_data)
            print(f"🎤 TRANSCRIPTION - Text: '{answer_text}'")
        else:
            answer_text = "No audio detected"
            print("⚠️ No valid audio data available for transcription")
        
        # Run the graph with voice analysis
        result = await interview_manager.step(
            user_id,
            session_id,
            user_answer=answer_text,
            audio_data=audio_data if audio_file else None
        )

        history = result.get("history", [])
        last_item = history[-1] if history else {}
        next_question = last_item.get("question") if not result.get("completed") else None

        if result.get("completed"):
            evaluated_item = last_item
        else:
            evaluated_item = history[-2] if len(history) >= 2 else {}

        response_data = {
            "evaluation": evaluated_item.get("evaluation"),
            "technical": evaluated_item.get("technical_evaluation"),
            "communication": evaluated_item.get("communication_evaluation"),
            "video_analysis": video_analysis,
            "next_question": next_question,
            "state": result,
        }
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in submit_answer: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": f"Internal server error: {str(e)}"})


@router.get("/debug/sessions")
def debug_sessions():
    """
    Debug endpoint to list all active sessions.
    """
    sessions = {}
    for key, state in interview_manager.sessions.items():
        sessions[key] = {
            "user_id": state.user_id,
            "session_id": state.session_id,
            "role_title": state.role_title,
            "status": "completed" if state.completed else "active",
            "question_count": state.question_count
        }
    return {"active_sessions": sessions, "total_count": len(sessions)}


@router.get("/state/{user_id}/{session_id}")
def get_state(user_id: str, session_id: str):
    """
    Get the current interview state for a given session.
    """
    state = interview_manager.get_state(user_id, session_id)
    if not state:
        raise HTTPException(status_code=404, detail={"error": "Session not found"})
    return state


@router.get("/sessions/{user_id}")
def get_user_sessions(user_id: str):
    """
    Get all interview sessions for a specific user.
    """
    sessions = interview_manager.get_user_sessions(user_id)
    if not sessions:
        raise HTTPException(status_code=404, detail={"error": "No sessions found for user"})
    return sessions


@router.get("/report/{user_id}/{session_id}", response_model=ReportResponse)
def get_report(user_id: str, session_id: str):
    """
    Generate a structured summary report for an interview session.
    """
    report = interview_manager.generate_report(user_id, session_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report)
    return report
