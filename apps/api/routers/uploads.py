import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import aiofiles

from core.config import settings
from core.db import get_db
from core.models import User, Artifact
from core.schemas import UploadResponse
from apps.api.deps.auth import get_current_active_user
from ingest.extract import extract_text_from_file
from ingest.normalize import normalize_cv, normalize_jd

router = APIRouter(prefix="/uploads", tags=["uploads"])


async def save_upload_file(upload_file: UploadFile, folder: str) -> str:
    """Save uploaded file to disk"""
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.upload_dir, folder), exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, folder, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    
    return file_path


@router.post("/cv", response_model=UploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a CV document"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith(('application/pdf', 'text/')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and text files are supported"
        )
    
    # Validate file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {settings.max_file_size} bytes"
        )
    
    try:
        # Save file
        file_path = await save_upload_file(file, "cv")
        
        # Extract text from file
        text = await extract_text_from_file(file_path)
        
        # Normalize CV data
        normalized_data = normalize_cv(text)
        
        # Create artifact record
        artifact = Artifact(
            type="cv",
            path=file_path,
            text=text,
            meta={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": file.size,
                "normalized_data": normalized_data
            }
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return UploadResponse(
            artifact_id=artifact.id,
            type="cv",
            path=file_path
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CV upload: {str(e)}"
        )


@router.post("/jd", response_model=UploadResponse)
async def upload_jd(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a job description document"""
    # Validate file type
    if not file.content_type or not file.content_type.startswith(('application/pdf', 'text/')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and text files are supported"
        )
    
    # Validate file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {settings.max_file_size} bytes"
        )
    
    try:
        # Save file
        file_path = await save_upload_file(file, "jd")
        
        # Extract text from file
        text = await extract_text_from_file(file_path)
        
        # Normalize JD data
        normalized_data = normalize_jd(text)
        
        # Create artifact record
        artifact = Artifact(
            type="jd",
            path=file_path,
            text=text,
            meta={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": file.size,
                "normalized_data": normalized_data
            }
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return UploadResponse(
            artifact_id=artifact.id,
            type="jd",
            path=file_path
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process JD upload: {str(e)}"
        )


@router.get("/cv/{artifact_id}")
async def get_cv(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get CV artifact details"""
    artifact = db.query(Artifact).filter(
        Artifact.id == artifact_id,
        Artifact.type == "cv"
    ).first()
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV artifact not found"
        )
    
    return {
        "id": artifact.id,
        "type": artifact.type,
        "text": artifact.text,
        "meta": artifact.meta,
        "created_at": artifact.created_at
    }


@router.get("/jd/{artifact_id}")
async def get_jd(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get JD artifact details"""
    artifact = db.query(Artifact).filter(
        Artifact.id == artifact_id,
        Artifact.type == "jd"
    ).first()
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD artifact not found"
        )
    
    return {
        "id": artifact.id,
        "type": artifact.type,
        "text": artifact.text,
        "meta": artifact.meta,
        "created_at": artifact.created_at
    }


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an artifact"""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    
    try:
        # Remove file from disk
        if os.path.exists(artifact.path):
            os.remove(artifact.path)
        
        # Remove from database
        db.delete(artifact)
        db.commit()
        
        return {"message": "Artifact deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete artifact: {str(e)}"
        )
