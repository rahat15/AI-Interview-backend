# apps/api/routers/cv.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List

from apps.api.deps import get_engine
from cv_eval.schemas import CVEvaluationRequest
from cv_eval.engine import CVEvaluationEngine

router = APIRouter(
    prefix="/v1/cv",
    tags=["cv"],
    # dependencies=[Depends(auth.require_user)]  # uncomment if you want auth
)

# ---------- Request DTOs ----------
class CVScoreRequest(BaseModel):
    cv_text: str = Field(..., description="Raw resume text")

class FitIndexRequest(BaseModel):
    cv_text: str = Field(..., description="Raw resume text")
    jd_text: str = Field(..., description="Raw job description text")
    include_constraints: bool = True

# ---------- Response DTOs (dashboard-friendly) ----------
class SubscoreDTO(BaseModel):
    dimension: str
    score: float
    max_score: float
    evidence: List[str] = []

class SectionScoreDTO(BaseModel):
    score: float
    band: str
    subscores: List[SubscoreDTO]

class FitIndexResponseDTO(BaseModel):
    fit_index: dict
    cv_quality: SectionScoreDTO
    jd_match: SectionScoreDTO

@router.post("/score", response_model=SectionScoreDTO, summary="Score CV Quality")
def score_cv(payload: CVScoreRequest, engine: CVEvaluationEngine = Depends(get_engine)):
    try:
        cv_report = engine.evaluate_cv_quality(payload.cv_text)
        return SectionScoreDTO(
            score=round(cv_report.overall_score, 2),
            band=cv_report.band,
            subscores=[
                SubscoreDTO(
                    dimension=s.dimension,
                    score=round(s.score, 2),
                    max_score=s.max_score,
                    evidence=s.evidence or []
                ) for s in cv_report.subscores
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV scoring failed: {e}")

@router.post("/fit-index", response_model=FitIndexResponseDTO, summary="Score CV + JD (Fit Index)")
def score_fit_index(payload: FitIndexRequest, engine: CVEvaluationEngine = Depends(get_engine)):
    try:
        result = engine.evaluate(CVEvaluationRequest(
            cv_text=payload.cv_text,
            jd_text=payload.jd_text,
            include_constraints=payload.include_constraints
        ))
        return FitIndexResponseDTO(
            fit_index={"score": result.fit_index, "band": result.band},
            cv_quality=SectionScoreDTO(
                score=round(result.cv_quality.overall_score, 2),
                band=result.cv_quality.band,
                subscores=[
                    SubscoreDTO(
                        dimension=s.dimension,
                        score=round(s.score, 2),
                        max_score=s.max_score,
                        evidence=s.evidence or []
                    ) for s in result.cv_quality.subscores
                ],
            ),
            jd_match=SectionScoreDTO(
                score=round(result.jd_match.overall_score, 2),
                band=result.jd_match.band,
                subscores=[
                    SubscoreDTO(
                        dimension=s.dimension,
                        score=round(s.score, 2),
                        max_score=s.max_score,
                        evidence=s.evidence or []
                    ) for s in result.jd_match.subscores
                ],
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fit Index scoring failed: {e}")
