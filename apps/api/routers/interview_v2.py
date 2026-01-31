"""
V2 Interview API Routes - Gemini-powered interviews
Provides clean, working endpoints without LangGraph complexity
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Dict, Any, Optional
import uuid
from bson import ObjectId
import tempfile
import os

from core.schemas import (
    InterviewV2StartResponse,
    InterviewV2AnswerRequest,
    InterviewV2AnswerResponse,
    InterviewV2CompleteResponse
)
from interview.gemini_interviewer import gemini_interviewer
from interview.voice_analyzer import VoiceAnalyzer
from core.db import get_database

router = APIRouter(prefix="/v2/interview")
voice_analyzer = VoiceAnalyzer(sample_rate=16000)


async def fetch_resume_content(resume_id: str) -> str:
    """Fetch resume content from MongoDB"""
    db = await get_database()
    
    # Try multiple query methods
    resume_doc = None
    if ObjectId.is_valid(resume_id):
        resume_doc = await db.resumes.find_one({"_id": ObjectId(resume_id)})
    
    if not resume_doc:
        resume_doc = await db.resumes.find_one({"_id": resume_id})
    
    if not resume_doc:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found")
    
    # Extract text from stats or path
    resume_text = ""
    
    # Try to get extracted text from stats
    if "stats" in resume_doc and resume_doc["stats"]:
        stats = resume_doc["stats"]
        if "extractedText" in stats:
            resume_text = stats["extractedText"]
        elif "text" in stats:
            resume_text = stats["text"]
    
    # Fallback: try to read from file path
    if not resume_text and "path" in resume_doc:
        try:
            import aiofiles
            file_path = resume_doc["path"]
            if file_path.startswith("uploads/"):
                async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
                    resume_text = await f.read()
        except Exception as e:
            print(f"Could not read resume file: {e}")
    
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Resume content not available. Please re-upload the resume."
        )
    
    return resume_text


async def fetch_jd_content(jd_id: str) -> str:
    """Fetch job description content from MongoDB"""
    db = await get_database()
    
    # Try multiple query methods
    jd_doc = None
    if ObjectId.is_valid(jd_id):
        jd_doc = await db.jobdescriptions.find_one({"_id": ObjectId(jd_id)})
    
    if not jd_doc:
        jd_doc = await db.jobdescriptions.find_one({"_id": jd_id})
    
    if not jd_doc:
        raise HTTPException(status_code=404, detail=f"Job description {jd_id} not found")
    
    # Extract text
    jd_text = jd_doc.get("text", "")
    
    # Fallback: try to read from file path
    if not jd_text and "path" in jd_doc:
        try:
            import aiofiles
            file_path = jd_doc["path"]
            if file_path.startswith("uploads/"):
                async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
                    jd_text = await f.read()
        except Exception as e:
            print(f"Could not read JD file: {e}")
    
    if not jd_text:
        raise HTTPException(
            status_code=400,
            detail="Job description content not available. Please re-upload the JD."
        )
    
    return jd_text


async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from uploaded file (PDF, DOCX, TXT)"""
    content = await file.read()
    filename = file.filename.lower()
    
    try:
        # Text files
        if filename.endswith('.txt'):
            return content.decode('utf-8', errors='ignore')
        
        # PDF files
        elif filename.endswith('.pdf'):
            from pypdf import PdfReader
            import io
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        
        # Word documents
        elif filename.endswith('.docx'):
            from docx import Document
            import io
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {filename}. Please upload PDF, DOCX, or TXT files."
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error extracting text from {filename}: {str(e)}"
        )


# NOTE: removed the JSON-body start endpoint to avoid duplicate OpenAPI entries.


@router.post("/start", response_model=InterviewV2StartResponse)
async def start_interview(
    role: str = Form(..., description="Job role/position"),
    company: str = Form(default="the company", description="Company name"),
    resume_text: Optional[str] = Form(None, description="Resume as text (optional if uploading file)"),
    jd_text: Optional[str] = Form(None, description="JD as text (optional if uploading file)"),
    resume_file: Optional[UploadFile] = File(None, description="Resume file (PDF, DOCX, TXT)"),
    jd_file: Optional[UploadFile] = File(None, description="JD file (PDF, DOCX, TXT)")
):
    """Start interview by uploading resume and/or JD files (multipart/form-data).

    You may provide either files or text (or mix). Files take priority over text.
    """
    try:
        resume_content = None
        # File takes priority
        if resume_file:
            resume_content = await extract_text_from_file(resume_file)
        elif resume_text:
            resume_content = resume_text

        if not resume_content or not resume_content.strip():
            raise HTTPException(
                status_code=400,
                detail="Resume is required. Provide either resume_file or resume_text."
            )

        # JD content
        jd_content = None
        if jd_file:
            jd_content = await extract_text_from_file(jd_file)
        elif jd_text:
            jd_content = jd_text

        if not jd_content or not jd_content.strip():
            raise HTTPException(
                status_code=400,
                detail="Job Description is required. Provide either jd_file or jd_text."
            )

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        result = gemini_interviewer.create_session(
            session_id=session_id,
            resume_text=resume_content,
            jd_text=jd_content,
            role=role,
            company=company
        )

        return InterviewV2StartResponse(
            session_id=result["session_id"],
            status=result["status"],
            question=result["question"],
            question_number=result["question_number"],
            message="Interview started successfully with Gemini AI"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")


@router.post("/{session_id}/answer", response_model=InterviewV2AnswerResponse)
async def submit_answer(
    session_id: str,
    answer: Optional[str] = Form(None, description="Answer text (optional if audio provided)"),
    answer_audio: Optional[UploadFile] = File(None, description="Audio file (WAV, MP3, M4A, etc.)")
):
    """
    Submit an answer (text or audio) and get the next question
    
    - Accepts either text answer or audio file
    - Analyzes voice if audio provided
    - Records candidate's answer
    - Generates contextual follow-up question
    - Maintains conversation flow
    """
    try:
        answer_text = answer
        voice_metrics = None
        
        # Process audio if provided
        if answer_audio:
            # Read audio bytes
            audio_bytes = await answer_audio.read()
            
            # Transcribe using Gemini
            mime_type = answer_audio.content_type or "audio/wav"
            answer_text = gemini_interviewer.transcribe_audio(audio_bytes, mime_type)
            
            # Analyze voice
            voice_analysis = voice_analyzer.analyze_voice(audio_data=audio_bytes, transcript=answer_text)
            
            if voice_analysis.get("analysis_ok"):
                voice_metrics = {
                    "rate_wpm": voice_analysis.get("rate_wpm", 0),
                    "fluency_score": voice_analysis.get("scores_out_of_10", {}).get("fluency", 0),
                    "clarity_score": voice_analysis.get("scores_out_of_10", {}).get("clarity", 0),
                    "confidence_score": voice_analysis.get("scores_out_of_10", {}).get("confidence", 0),
                    "pace_score": voice_analysis.get("scores_out_of_10", {}).get("pace", 0),
                    "total_score": voice_analysis.get("scores_out_of_10", {}).get("total", 0),
                    "pitch_mean_hz": voice_analysis.get("pitch_mean_hz", 0),
                    "pitch_std_hz": voice_analysis.get("pitch_std_hz", 0),
                    "pause_ratio": voice_analysis.get("pause_ratio", 0)
                }
        
        if not answer_text or not answer_text.strip():
            raise HTTPException(status_code=400, detail="Either 'answer' text or 'answer_audio' file is required")
        
        result = gemini_interviewer.submit_answer(
            session_id=session_id,
            answer=answer_text,
            voice_metrics=voice_metrics
        )
        
        return InterviewV2AnswerResponse(
            session_id=result["session_id"],
            status=result["status"],
            question=result["question"],
            question_number=result["question_number"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")


@router.post("/{session_id}/complete", response_model=InterviewV2CompleteResponse)
async def complete_interview(session_id: str):
    """
    Complete the interview and get comprehensive analytics
    
    - Ends the interview session
    - Generates detailed evaluation from Gemini
    - Provides video analytics (sample data)
    - Returns full conversation history
    - Includes performance metrics and recommendations
    """
    try:
        result = gemini_interviewer.end_interview(session_id)
        
        return InterviewV2CompleteResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing interview: {str(e)}")


@router.get("/{session_id}/status")
async def get_interview_status(session_id: str):
    """
    Get current interview session status
    
    Returns current state of the interview session
    """
    try:
        result = gemini_interviewer.get_session_status(session_id)
        
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching status: {str(e)}")
