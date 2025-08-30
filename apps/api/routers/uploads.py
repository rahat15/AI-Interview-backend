import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File
import aiofiles

from core.config import settings
from ingest.extract import extract_text_from_file
from ingest.normalize import normalize_cv, normalize_jd

router = APIRouter(prefix="/uploads", tags=["uploads"])

# ── In-memory store instead of DB ─────────────
_artifacts = {}

# ── Helper: Save uploaded file ───────────────
async def save_upload_file(upload_file: UploadFile, folder: str) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    folder_path = os.path.join(settings.upload_dir, folder)
    os.makedirs(folder_path, exist_ok=True)

    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(folder_path, filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await upload_file.read()
        await out_file.write(content)

    return file_path


# ── Endpoints ────────────────────────────────
@router.post("/cv")
async def upload_cv(file: UploadFile = File(...)):
    """Upload a CV (mock, no DB)."""
    if not file.content_type or not file.content_type.startswith(("application/pdf", "text/")):
        raise HTTPException(status_code=400, detail="Only PDF and text files are supported")

    try:
        path = await save_upload_file(file, "cv")
        text = await extract_text_from_file(path)
        normalized = normalize_cv(text)

        art_id = uuid.uuid4()
        _artifacts[art_id] = {
            "id": art_id,
            "type": "cv",
            "path": path,
            "text": text,
            "meta": {
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(text),
                "normalized_data": normalized,
            },
        }
        return {"artifact_id": art_id, "type": "cv", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CV: {e}")


@router.post("/jd")
async def upload_jd(file: UploadFile = File(...)):
    """Upload a JD (mock, no DB)."""
    if not file.content_type or not file.content_type.startswith(("application/pdf", "text/")):
        raise HTTPException(status_code=400, detail="Only PDF and text files are supported")

    try:
        path = await save_upload_file(file, "jd")
        text = await extract_text_from_file(path)
        normalized = normalize_jd(text)

        art_id = uuid.uuid4()
        _artifacts[art_id] = {
            "id": art_id,
            "type": "jd",
            "path": path,
            "text": text,
            "meta": {
                "original_filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(text),
                "normalized_data": normalized,
            },
        }
        return {"artifact_id": art_id, "type": "jd", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process JD: {e}")


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: uuid.UUID):
    """Get artifact details (mock)."""
    art = _artifacts.get(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return art


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: uuid.UUID):
    """Delete artifact (mock)."""
    art = _artifacts.pop(artifact_id, None)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")

    try:
        if os.path.exists(art["path"]):
            os.remove(art["path"])
        return {"message": "Artifact deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete artifact: {e}")
