from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import tempfile
import os

from interview.speech_to_text import speech_converter
from interview.voice_analyzer import VoiceAnalyzer
from interview.video_analyzer import video_analyzer
from core.models import Session as SessionModel, Answer
from core.schemas import AnswerCreate
import uuid
from datetime import datetime

router = APIRouter()
voice_analyzer = VoiceAnalyzer()

@router.post("/{session_id}/answer")
async def submit_audio_answer(
    session_id: str,
    question_id: str = Form(...),
    audio_file: UploadFile = File(None),
    video_file: UploadFile = File(None)
):
    """Submit audio/video answer with speech-to-text, voice analysis, and video behavior analysis.

    Supports:
    - Audio only: Speech-to-text + voice analysis
    - Video only: Extract audio + video behavior analysis
    - Both: Complete analysis with all features
    """
    try:
        # Validate session exists
        session = await SessionModel.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if not audio_file and not video_file:
            raise HTTPException(status_code=400, detail="Either audio or video file is required")

        transcribed_text = ""
        voice_analysis = None
        video_analysis = None

        # Process video if provided
        if video_file:
            video_data = await video_file.read()
            
            # Video analysis
            video_analysis = video_analyzer.analyze_video(video_data)
            
            # Extract audio from video for transcription
            # Note: For now, if video is provided, audio_file should also be provided
            # In production, you'd extract audio from video using ffmpeg
            if not audio_file:
                raise HTTPException(
                    status_code=400, 
                    detail="Audio file required when submitting video (audio extraction from video not yet implemented)"
                )

        # Process audio
        if audio_file:
            audio_data = await audio_file.read()
            transcribed_text = speech_converter.convert_audio_to_text(audio_data)
            voice_analysis = voice_analyzer.analyze_voice(audio_data=audio_data)

        # Delegate to interview manager
        from interview.session_manager import interview_manager

        result = await interview_manager.step(
            user_id=session.user_id if hasattr(session, 'user_id') else session_id,
            session_id=session.id if hasattr(session, 'id') else session_id,
            user_answer=transcribed_text,
            audio_data=audio_data if audio_file else None,
        )

        history = result.get("history", [])
        last_item = history[-1] if history else {}
        evaluated_item = history[-2] if len(history) >= 2 else {}

        return {
            "evaluation": evaluated_item.get("evaluation"),
            "technical": evaluated_item.get("technical_evaluation"),
            "communication": evaluated_item.get("communication_evaluation"),
            "voice_analysis": voice_analysis,
            "video_analysis": video_analysis,
            "next_question": last_item.get("question") if not result.get("completed") else None,
            "state": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio/video: {str(e)}")

@router.post("/analyze")
async def analyze_audio_only(
    audio_file: UploadFile = File(None),
    video_file: UploadFile = File(None)
):
    """Analyze audio/video file for characteristics only (no session required)
    
    Supports:
    - Audio only: Speech-to-text + voice analysis
    - Video only: Video behavior analysis
    - Both: Complete analysis
    """
    try:
        if not audio_file and not video_file:
            raise HTTPException(status_code=400, detail="Either audio or video file is required")
        
        result = {}
        
        # Process audio
        if audio_file:
            audio_data = await audio_file.read()
            transcribed_text = speech_converter.convert_audio_to_text(audio_data=audio_data)
            voice_analysis = voice_analyzer.analyze_voice(
                audio_data=audio_data,
                transcript=transcribed_text
            )
            result["transcribed_text"] = transcribed_text
            result["voice_analysis"] = voice_analysis
        
        # Process video
        if video_file:
            video_data = await video_file.read()
            video_analysis = video_analyzer.analyze_video(video_data)
            result["video_analysis"] = video_analysis
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing audio/video: {str(e)}")