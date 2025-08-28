from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

#from core.db import get_db
from core.models import User, Artifact
from apps.api.deps.auth import get_current_active_user
from cv_eval.schemas import CVEvaluationRequest
from cv_eval.engine import CVEvaluationEngine

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# Initialize evaluation engine
evaluation_engine = CVEvaluationEngine()


@router.post("/cv")
async def evaluate_cv_jd(
    request: CVEvaluationRequest,
    current_user: User = Depends(get_current_active_user),
    #db: Session = Depends(get_db),
):
    """
    Evaluate CV against Job Description and return raw JSON from the engine.
    """
    try:
        if not request.cv_text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CV text cannot be empty")
        if not request.jd_text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text cannot be empty")

        result = evaluation_engine.evaluate(request)  # now returns dict/json
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )
