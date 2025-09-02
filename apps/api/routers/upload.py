from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil, tempfile, os
import pdfplumber
from docx import Document
import textract

from apps.api.eval_engine_instance import evaluation_engine   # ✅ import from shared
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

def save_and_extract(upload: UploadFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.filename)[1]) as tmp:
        shutil.copyfileobj(upload.file, tmp)
        tmp_path = tmp.name
    text = extract_text(tmp_path)
    os.remove(tmp_path)
    return text

# -----------------------
# Endpoints
# -----------------------
@router.post("/cv_evaluate")
async def upload_and_evaluate_cv(
    file: UploadFile = File(...),
    jd_text: str = Form("", description="Optional JD text"),
    jd_file: UploadFile = File(None)
):
    """
    Upload CV (PDF/DOC/DOCX), and optionally JD (text or file).
    - If only CV is provided → CV-only evaluation
    - If JD text/file provided → full CV vs JD evaluation
    """
    try:
        cv_text = save_and_extract(file)

        # Case 1: JD provided as plain text
        if jd_text and jd_text.strip():
            return evaluation_engine.evaluate(cv_text, jd_text)

        # Case 2: JD provided as a file
        if jd_file is not None:
            jd_extracted = save_and_extract(jd_file)
            return evaluation_engine.evaluate(cv_text, jd_extracted)

        # Case 3: Only CV (CV quality evaluation)
        return evaluation_engine.evaluate(cv_text)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Evaluation failed: {str(e)}")
