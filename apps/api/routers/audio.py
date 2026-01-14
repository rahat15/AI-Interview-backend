from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import tempfile
import os

from interview.speech_to_text import speech_converter
from interview.voice_analyzer import VoiceAnalyzer
from core.models import Session as SessionModel, Answer
from core.schemas import AnswerCreate
import uuid
from datetime import datetime

router = APIRouter(prefix="/audio", tags=["audio"])
voice_analyzer = VoiceAnalyzer()

@router.post("/{session_id}/answer")
async def submit_audio_answer(
    session_id: str,
    question_id: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """Submit audio answer and run the unified interview step (ASR + voice analysis + technical evaluation).

    This endpoint delegates to the interview manager step so the behavior matches the main `/answer` flow.
    """
    try:
        # Validate session exists (SessionModel here may be a thin wrapper; keep validation)
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if not audio_file:
            raise HTTPException(status_code=400, detail="Audio file is required")

        audio_data = await audio_file.read()

        # Convert speech to text
        transcribed_text = speech_converter.convert_audio_to_text(
            audio_data=audio_data,
            filename=audio_file.filename
        )

        # Delegate to interview manager (it will perform technical LLM eval and voice analysis)
        from interview.session_manager import interview_manager

        # Here we pass the audio_data and transcribed text via the unified step
        result = await interview_manager.step(
            user_id=session.user_id if hasattr(session, 'user_id') else session_id,
            session_id=session.id if hasattr(session, 'id') else session_id,
            user_answer=transcribed_text,
            audio_data=audio_data,
        )

        history = result.get("history", [])
        last_item = history[-1] if history else {}
        evaluated_item = history[-2] if len(history) >= 2 else {}

        return {
            "evaluation": evaluated_item.get("evaluation"),
            "technical": evaluated_item.get("technical_evaluation"),
            "communication": evaluated_item.get("communication_evaluation"),
            "next_question": last_item.get("question") if not result.get("completed") else None,
            "state": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@router.post("/analyze")
async def analyze_audio_only(
    audio_file: UploadFile = File(...)
):
    """Analyze audio file for voice characteristics only (no session required)"""
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Convert speech to text
        transcribed_text = speech_converter.convert_audio_to_text(
            audio_data=audio_data,
            filename=audio_file.filename
        )

        
        # Analyze voice characteristics
        voice_analysis = voice_analyzer.analyze_voice(
            audio_data=audio_data,
            transcript=transcribed_text
        )

        
        return {
            "transcribed_text": transcribed_text,
            "voice_analysis": voice_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing audio: {str(e)}")