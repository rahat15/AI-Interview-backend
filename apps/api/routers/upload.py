from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil, tempfile, os
import pdfplumber
from docx import Document
import textract

# Import your evaluation engine and schema
from apps.api.routers.evaluation import evaluation_engine
from cv_eval.schemas import CVEvaluationResult

router = APIRouter(prefix="/upload", tags=["upload"])

# -----------------------
# Helpers
# -----------------------
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
            text += "\n"
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_doc(file_path: str) -> str:
    return textract.process(file_path).decode("utf-8")

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".doc":
        return extract_text_from_doc(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

# -----------------------
# Endpoints
# -----------------------
@router.post("/cv")
async def upload_cv(file: UploadFile = File(...)):
    """Extracts text only (no evaluation)"""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        text = extract_text(tmp_path)
        return {"cv_text": text}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        file.file.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/cv_evaluate", response_model=CVEvaluationResult)
async def upload_and_evaluate_cv(file: UploadFile = File(...)):
    """Uploads CV (PDF/DOC/DOCX), extracts text, and evaluates it"""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        text = extract_text(tmp_path)

        # Directly run evaluation on extracted text
        result = evaluation_engine.evaluate(text)  
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        file.file.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
