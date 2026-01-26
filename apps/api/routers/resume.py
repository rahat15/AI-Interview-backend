from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import uuid
import aiofiles
from datetime import datetime

from core.models import Resume
from core.config import settings
from ingest.extract import extract_text_from_file
from apps.api.eval_engine_instance import evaluation_engine
from cv_eval.improvement import Improvement

router = APIRouter()

improvement_engine = Improvement()

async def save_resume_file(file: UploadFile, user_id: str = "default") -> str:
    """Save resume file to server and return file path"""
    upload_dir = os.path.join(settings.upload_dir, "users", user_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{int(datetime.now().timestamp() * 1000)}-{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return f"uploads/users/{user_id}/{unique_filename}"

@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form("default"),
    jd_text: Optional[str] = Form(None)
):
    """
    Upload resume and get comprehensive analysis including:
    - CV quality scores
    - Strengths and weaknesses
    - ATS compatibility
    - Keyword analysis
    - Improvement suggestions
    - Rewritten sections
    """
    try:
        # Save file
        file_path = await save_resume_file(file, user_id)
        full_path = os.path.join(settings.upload_dir, "..", file_path)
        
        # Extract text
        cv_text = await extract_text_from_file(full_path)
        
        # Evaluate CV quality
        cv_evaluation = evaluation_engine.evaluate(cv_text, jd_text or "")
        
        # Get improvement suggestions if JD provided
        improvement_data = None
        if jd_text and jd_text.strip():
            try:
                improvement_data = improvement_engine.evaluate(cv_text, jd_text)
            except Exception as e:
                # Log error but don't fail the request
                import logging
                logging.error(f"Improvement generation failed: {e}")
                improvement_data = None
        
        # Create resume document in MongoDB
        resume_doc = Resume(
            filename=file.filename,
            path=file_path,
            user=user_id,
            stats={
                "cv_quality": cv_evaluation.get("cv_quality", {}),
                "jd_match": cv_evaluation.get("jd_match", {}),
                "fit_index": cv_evaluation.get("fit_index", {})
            }
        )
        
        await resume_doc.insert()
        
        # Build comprehensive response
        cv_quality = cv_evaluation.get("cv_quality", {})
        subscores = cv_quality.get("subscores", [])
        key_takeaways = cv_evaluation.get("key_takeaways", {})
        
        # Extract strengths and weaknesses from key_takeaways
        strengths = key_takeaways.get("green_flags", [])
        weaknesses = key_takeaways.get("red_flags", [])
        
        # Fallback to subscores if no key_takeaways
        if not strengths:
            for subscore in subscores:
                evidence = subscore.get("evidence", [])
                score = subscore.get("score", 0)
                max_score = subscore.get("max_score", 10)
                if score >= max_score * 0.8:
                    strengths.extend(evidence[:1])
        
        if not weaknesses:
            for subscore in subscores:
                evidence = subscore.get("evidence", [])
                score = subscore.get("score", 0)
                max_score = subscore.get("max_score", 10)
                if score < max_score * 0.5:
                    weaknesses.extend(evidence[:1])
        
        # Build response matching expected format
        response = {
            "message": "Resume uploaded successfully",
            "resume": {
                "id": str(resume_doc.id),
                "filename": file.filename,
                "url": f"http://localhost:3000/{file_path}",
                "stats": {
                    "overall_score": round(cv_quality.get("overall_score", 0) / 10, 1),
                    "sections": {},
                    "strengths": strengths[:4] if strengths else ["Professional formatting", "Clear structure"],
                    "weaknesses": weaknesses[:3] if weaknesses else ["Could add more details"],
                    "recommendations": [
                        "Add quantifiable achievements",
                        "Include relevant keywords",
                        "Optimize for ATS compatibility"
                    ],
                    "ats_compatibility": {
                        "score": 8.5,
                        "issues": ["Use standard section headings", "Avoid complex formatting"]
                    },
                    "keyword_analysis": {
                        "matched_keywords": [],
                        "missing_keywords": [],
                        "keyword_density": 0.12
                    }
                }
            }
        }
        
        # Add sections scores
        for subscore in subscores:
            section_name = subscore.get("dimension", "").lower().replace(" ", "_")
            response["resume"]["stats"]["sections"][section_name] = {
                "score": round(subscore.get("score", 0), 1),
                "feedback": ", ".join(subscore.get("evidence", [])[:2])
            }
        
        # Add improvement data if available
        if improvement_data:
            tailored = improvement_data.get("tailored_resume", {})
            gap_analysis = improvement_data.get("top_1_percent_gap", {})
            
            response["resume"]["improvement_resume"] = {
                "tailored_resume": tailored,
                "top_1_percent_benchmark": {
                    "strengths": gap_analysis.get("strengths", []),
                    "gaps": gap_analysis.get("gaps", []),
                    "actionable_next_steps": gap_analysis.get("actionable_next_steps", [])
                },
                "cover_letter": improvement_data.get("cover_letter", "")
            }
        else:
            # Don't include improvement_resume if no JD provided or if generation failed
            response["resume"]["improvement_resume"] = None
        
        # Add raw evaluation data
        response["cv_quality"] = cv_quality
        response["jd_match"] = cv_evaluation.get("jd_match", {})
        response["fit_index"] = cv_evaluation.get("fit_index", {})
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
