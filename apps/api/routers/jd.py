from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
import uuid
import aiofiles
from datetime import datetime

from core.models import JobDescription
from core.config import settings

router = APIRouter(prefix="/jd", tags=["Job Description Management"])

async def save_jd_file(file: UploadFile, user_id: str = "default") -> str:
    """Save JD file to server and return file path"""
    # Create uploads directory
    upload_dir = os.path.join(settings.upload_dir, "jd")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return f"uploads/jd/{unique_filename}"

@router.post("/upload")
async def upload_jd(
    file: UploadFile = File(...),
    user_id: str = Form("default")
):
    """Upload JD file and store in MongoDB"""
    try:
        # Save file to server
        file_path = await save_jd_file(file, user_id)
        
        # Extract text content (basic implementation)
        text_content = ""
        if file.content_type == "text/plain":
            content = await file.read()
            text_content = content.decode('utf-8')
        
        # Create JD document in MongoDB
        jd_doc = JobDescription(
            filename=file.filename,
            path=file_path,
            text=text_content,
            user=user_id
        )
        
        await jd_doc.insert()
        
        return {
            "id": str(jd_doc.id),
            "filename": jd_doc.filename,
            "path": jd_doc.path,
            "user": jd_doc.user,
            "created_at": jd_doc.created_at,
            "message": "JD uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{jd_id}")
async def get_jd(jd_id: str):
    """Get JD by ID"""
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
        
        if not jd_doc:
            raise HTTPException(status_code=404, detail="JD not found")
        
        return {
            "id": str(jd_doc["_id"]),
            "filename": jd_doc.get("filename", ""),
            "path": jd_doc.get("path", ""),
            "text": jd_doc.get("text", ""),
            "user": jd_doc.get("user", ""),
            "created_at": jd_doc.get("createdAt")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching JD: {str(e)}")

@router.get("/")
async def list_jds(user_id: Optional[str] = None):
    """List all JDs or by user"""
    try:
        from core.db import get_database
        db = await get_database()
        
        query = {}
        if user_id:
            query["user"] = user_id
        
        jds = await db.jobdescriptions.find(query).to_list(length=100)
        
        return {
            "total": len(jds),
            "jds": [
                {
                    "id": str(jd["_id"]),
                    "filename": jd.get("filename", ""),
                    "user": jd.get("user", ""),
                    "created_at": jd.get("createdAt")
                }
                for jd in jds
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing JDs: {str(e)}")

@router.delete("/{jd_id}")
async def delete_jd(jd_id: str):
    """Delete JD by ID"""
    try:
        from bson import ObjectId
        from core.db import get_database
        
        db = await get_database()
        
        # Find and delete JD
        if ObjectId.is_valid(jd_id):
            result = await db.jobdescriptions.delete_one({"_id": ObjectId(jd_id)})
        else:
            result = await db.jobdescriptions.delete_one({"_id": jd_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="JD not found")
        
        return {"message": "JD deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting JD: {str(e)}")