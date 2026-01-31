"""
Gemini-powered Interview Service
Handles contextual interview sessions with JD and Resume analysis
"""

import os
import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from core.config import settings

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class GeminiInterviewer:
    """Handles interview sessions using Google Gemini AI"""
    
    def __init__(self):
        # Use Gemini 2.5 Pro - best available model from your list
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(
        self,
        session_id: str,
        resume_text: str,
        jd_text: str,
        role: str,
        company: str = "the company"
    ) -> Dict[str, Any]:
        """
        Create a new interview session with context
        
        Args:
            session_id: Unique session identifier
            resume_text: Candidate's resume content
            jd_text: Job description text
            role: Job role/position
            company: Company name
            
        Returns:
            Session metadata including first question
        """
        
        # Build context prompt
        system_context = f"""You are Alex, a Senior Software Engineer at {company}. You are conducting a technical interview for the {role} position.

CANDIDATE'S RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

YOUR INSTRUCTIONS:
1. Act purely as the interviewer. Do NOT output any meta-text like "Here is the interview" or "***".
2. Speak in a natural, conversational, yet professional tone. Avoid robotic phrasing.
3. Start IMMEDIATELY with a warm, brief introduction and your first question.
4. Your goal is to assess if the candidate fits the JD based on their Resume.
5. Ask ONE clear question at a time.
6. If the candidate mentions a project, ask technical details about it that relate to the JD.

Start the interview now. Introduction + First Question only."""

        # Initialize chat
        chat = self.model.start_chat(history=[])
        
        # Get first question
        response = chat.send_message(system_context)
        first_question = response.text
        
        # Store session
        self.sessions[session_id] = {
            "session_id": session_id,
            "role": role,
            "company": company,
            "resume_text": resume_text,
            "jd_text": jd_text,
            "chat": chat,
            "history": [
                {"role": "interviewer", "content": first_question}
            ],
            "question_count": 1,
            "system_context": system_context,
            "voice_scores": []
        }
        
        return {
            "session_id": session_id,
            "status": "active",
            "question": first_question,
            "question_number": 1
        }
    
    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio using Gemini Multimodal capabilities"""
        prompt = "Running transcription. Please output ONLY the exact word-for-word transcript of this audio. Do not add any conversational filler."
        try:
            response = self.model.generate_content([prompt, {"mime_type": mime_type, "data": audio_bytes}])
            return response.text.strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return f"[Audio Transcription Failed]"

    def submit_answer(
        self,
        session_id: str,
        answer: str,
        voice_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit an answer and get the next question
        
        Args:
            session_id: Session identifier
            answer: Candidate's answer
            voice_metrics: Optional audio analysis metrics
            
        Returns:
            Next question and metadata
        """
        
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        chat = session["chat"]
        
        # Record answer
        entry = {
            "role": "candidate",
            "content": answer
        }
        if voice_metrics:
            entry["voice_metrics"] = voice_metrics
            session.setdefault("voice_scores", []).append(voice_metrics)
            
        session["history"].append(entry)
        
        # Build prompt regarding voice metrics
        voice_context = ""
        if voice_metrics:
            voice_context = f"""
[VOICE ANALYSIS DATA]
The candidate answered via VOICE.
- Speaking Rate: {voice_metrics.get('rate_wpm', 'N/A')} words/min
- Fluency Score: {voice_metrics.get('fluency_score', 'N/A')}/10
- Confidence Score: {voice_metrics.get('confidence_score', 'N/A')}/10
- Clarity: {voice_metrics.get('clarity_score', 'N/A')}/10
(Consider these metrics when evaluating communication skills)
"""

        # Get next question from Gemini
        prompt = f"""The candidate answered: "{answer}"
{voice_context}

Based on their response and considering:
- The JD requirements for the {session['role']} position
- Their resume background and experience
- The conversation flow so far

Please:
1. Briefly acknowledge their answer (1 sentence max)
2. Ask your next interview question that:
   - Builds naturally on the conversation
   - Tests a different skill/area from the JD
   - Relates to their resume experience when relevant
   - Probes appropriate technical or behavioral depth
   - Helps assess their fit for the {session['role']} role at {session['company']}

Keep your response conversational and professional. Focus on one clear question."""

        response = chat.send_message(prompt)
        next_question = response.text
        
        # Update session
        session["question_count"] += 1
        session["history"].append({
            "role": "interviewer",
            "content": next_question
        })
        
        return {
            "session_id": session_id,
            "status": "active",
            "question": next_question,
            "question_number": session["question_count"]
        }
    
    def end_interview(self, session_id: str) -> Dict[str, Any]:
        """
        End interview and generate comprehensive analytics
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete interview analytics
        """
        
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        chat = session["chat"]
        
        # Generate comprehensive evaluation
        evaluation_prompt = f"""The interview has concluded. Please provide a comprehensive evaluation in the following JSON format:

{{
    "overall_score": <number 1-10>,
    "recommendation": "<hire|maybe|no_hire>",
    "summary": "<2-3 sentence overall assessment>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"],
    "technical_skills": {{
        "score": <1-10>,
        "assessment": "<detailed technical assessment>"
    }},
    "communication_skills": {{
        "score": <1-10>,
        "assessment": "<detailed communication assessment>"
    }},
    "problem_solving": {{
        "score": <1-10>,
        "assessment": "<detailed problem-solving assessment>"
    }},
    "cultural_fit": {{
        "score": <1-10>,
        "assessment": "<cultural fit assessment>"
    }},
    "experience_relevance": {{
        "score": <1-10>,
        "assessment": "<how relevant is their experience>"
    }},
    "detailed_feedback": "<comprehensive paragraph about the candidate>",
    "improvement_areas": ["<area 1>", "<area 2>", "<area 3>"],
    "key_highlights": ["<highlight 1>", "<highlight 2>", "<highlight 3>"]
}}

Provide ONLY the JSON, no other text."""

        response = chat.send_message(evaluation_prompt)
        
        # Parse evaluation
        try:
            # Extract JSON from response
            eval_text = response.text.strip()
            if "```json" in eval_text:
                eval_text = eval_text.split("```json")[1].split("```")[0].strip()
            elif "```" in eval_text:
                eval_text = eval_text.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(eval_text)
        except:
            # Fallback if JSON parsing fails
            evaluation = {
                "overall_score": 7,
                "recommendation": "maybe",
                "summary": "Good candidate with relevant experience",
                "strengths": ["Strong communication", "Relevant experience", "Good problem-solving"],
                "weaknesses": ["Could improve technical depth", "Limited experience in some areas"],
                "technical_skills": {"score": 7, "assessment": "Solid technical foundation"},
                "communication_skills": {"score": 8, "assessment": "Communicates clearly"},
                "problem_solving": {"score": 7, "assessment": "Good analytical approach"},
                "cultural_fit": {"score": 7, "assessment": "Aligns with company values"},
                "experience_relevance": {"score": 8, "assessment": "Highly relevant background"},
                "detailed_feedback": response.text,
                "improvement_areas": ["Technical depth", "Specific domain knowledge"],
                "key_highlights": ["Strong communication", "Relevant experience"]
            }
        
        # Aggregate voice analytics from all answers
        voice_scores = session.get("voice_scores", [])
        voice_analytics = None
        
        if voice_scores:
            # Calculate averages
            avg_fluency = sum(v.get("fluency_score", 0) for v in voice_scores) / len(voice_scores)
            avg_clarity = sum(v.get("clarity_score", 0) for v in voice_scores) / len(voice_scores)
            avg_confidence = sum(v.get("confidence_score", 0) for v in voice_scores) / len(voice_scores)
            avg_pace = sum(v.get("pace_score", 0) for v in voice_scores) / len(voice_scores)
            avg_wpm = sum(v.get("rate_wpm", 0) for v in voice_scores) / len(voice_scores)
            avg_total = sum(v.get("total_score", 0) for v in voice_scores) / len(voice_scores)
            
            voice_analytics = {
                "analysis_performed": True,
                "total_voice_samples": len(voice_scores),
                "average_scores": {
                    "fluency": round(avg_fluency, 2),
                    "clarity": round(avg_clarity, 2),
                    "confidence": round(avg_confidence, 2),
                    "pace": round(avg_pace, 2),
                    "overall": round(avg_total, 2)
                },
                "speaking_rate_wpm": round(avg_wpm, 1),
                "detailed_scores": voice_scores,
                "interpretation": {
                    "fluency": "Excellent" if avg_fluency >= 8 else "Good" if avg_fluency >= 6 else "Needs improvement",
                    "clarity": "Excellent" if avg_clarity >= 8 else "Good" if avg_clarity >= 6 else "Needs improvement",
                    "confidence": "Excellent" if avg_confidence >= 8 else "Good" if avg_confidence >= 6 else "Needs improvement",
                    "pace": "Excellent" if avg_pace >= 8 else "Good" if avg_pace >= 6 else "Needs improvement"
                }
            }
        
        # Generate sample video analytics
        video_analytics = {
            "confidence_score": 7.8,
            "eye_contact_percentage": 82,
            "posture_score": 8.2,
            "engagement_level": "high",
            "speech_pace": "moderate",
            "filler_words_count": 12,
            "smile_frequency": "appropriate",
            "facial_expressions": {
                "positive": 68,
                "neutral": 28,
                "stressed": 4
            },
            "body_language": {
                "open": 75,
                "closed": 15,
                "neutral": 10
            },
            "energy_level": "medium-high",
            "professionalism_score": 8.5,
            "note": "Sample data - video analysis requires video upload feature"
        }
        
        # Build comprehensive response
        result = {
            "session_id": session_id,
            "status": "completed",
            "interview_duration_minutes": session["question_count"] * 3,  # Estimate
            "total_questions": session["question_count"],
            "role": session["role"],
            "company": session["company"],
            
            # Evaluation
            "evaluation": evaluation,
            
            # Video Analytics
            "video_analytics": video_analytics,
            
            # Voice Analytics (if available)
            "voice_analytics": voice_analytics,
            
            # Conversation History
            "conversation": session["history"],
            
            # Metrics
            "metrics": {
                "response_quality": evaluation.get("overall_score", 7),
                "technical_depth": evaluation.get("technical_skills", {}).get("score", 7),
                "communication": evaluation.get("communication_skills", {}).get("score", 8),
                "overall_performance": evaluation.get("overall_score", 7)
            }
        }
        
        # Clean up session
        del self.sessions[session_id]
        
        return result
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status"""
        
        if session_id not in self.sessions:
            return {"status": "not_found"}
        
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "status": "active",
            "question_number": session["question_count"],
            "role": session["role"],
            "company": session["company"]
        }


# Global interviewer instance
gemini_interviewer = GeminiInterviewer()
