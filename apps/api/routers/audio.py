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
    """Submit audio answer and get speech-to-text + voice analysis"""
    try:
        # Validate session exists
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Read audio file
        audio_data = await audio_file.read()
        
        # Convert speech to text
        transcribed_text = speech_converter.convert_audio_to_text(audio_data)
        
        # Analyze voice characteristics
        voice_analysis = voice_analyzer.analyze_voice(
            audio_data=audio_data,
            transcript=transcribed_text
        )

        # Create answer record
        answer_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "question_id": question_id,
            "text": transcribed_text,
            "asr_text": transcribed_text,
            "meta": {
                "has_audio": True,
                "voice_analysis": voice_analysis,
                "audio_filename": audio_file.filename
            },
            "created_at": datetime.utcnow()
        }
        
        answer = Answer(**answer_data)
        await answer.insert()
        
        return {
            "answer_id": answer.id,
            "transcribed_text": transcribed_text,
            "voice_analysis": voice_analysis,
            "message": "Audio answer processed successfully"
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
        transcribed_text = speech_converter.convert_audio_to_text(audio_data)
        
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