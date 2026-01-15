# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, Field
# from typing import List

# from cv_eval.schemas import CVEvaluationRequest
# from cv_eval.engine import CVEvaluationEngine

# router = APIRouter(
#     prefix="/v1/cv",
#     tags=["cv"],
# )

# # ---------- Init Engine ----------
# evaluation_engine = CVEvaluationEngine()

# # ---------- Request DTOs ----------
# class CVScoreRequest(BaseModel):
#     cv_text: str = Field(..., description="Raw resume text")

# class FitIndexRequest(BaseModel):
#     cv_text: str = Field(..., description="Raw resume text")
#     jd_text: str = Field(..., description="Raw job description text")
#     include_constraints: bool = True

# # ---------- Response DTOs (dashboard-friendly) ----------
# class SubscoreDTO(BaseModel):
#     dimension: str
#     score: float
#     max_score: float
#     evidence: List[str] = []

# class SectionScoreDTO(BaseModel):
#     score: float
#     band: str
#     subscores: List[SubscoreDTO]

# class FitIndexResponseDTO(BaseModel):
#     fit_index: dict
#     cv_quality: SectionScoreDTO
#     jd_match: SectionScoreDTO

    
# # ---------- Routes ----------
# @router.post("/score", response_model=SectionScoreDTO, summary="Score CV Quality")
# def score_cv(payload: CVScoreRequest):
#     try:
#         # Run evaluation (JD not needed here)
#         result = evaluation_engine.evaluate(
#             cv_text=payload.cv_text,
#             jd_text=""
#         )

#         # Always dict-safe
#         cv_quality = result.get("cv_quality", {})

#         return SectionScoreDTO(
#             score=round(cv_quality.get("overall_score", 0), 2),
#             band=cv_quality.get("band", "unknown"),
#             subscores=[
#                 SubscoreDTO(
#                     dimension=s.get("dimension", "unknown"),
#                     score=round(s.get("score", 0), 2),
#                     max_score=s.get("max_score", 0),
#                     evidence=s.get("evidence", []),
#                 )
#                 for s in cv_quality.get("subscores", [])
#             ],
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"CV scoring failed: {str(e)}")


# @router.post("/fit-index", response_model=FitIndexResponseDTO, summary="Score CV + JD (Fit Index)")
# def score_fit_index(payload: FitIndexRequest):
#     try:
#         # Run evaluation
#         result = evaluation_engine.evaluate(
#             cv_text=payload.cv_text,
#             jd_text=payload.jd_text
#         )

#         # Always dict-safe
#         cv_quality = result.get("cv_quality", {})
#         jd_match = result.get("jd_match", {})
#         fit_index = result.get("fit_index", {})

#         return FitIndexResponseDTO(
#             fit_index={
#                 "score": fit_index.get("score", 0),
#                 "band": fit_index.get("band", "unknown"),
#             },
#             cv_quality=SectionScoreDTO(
#                 score=round(cv_quality.get("overall_score", 0), 2),
#                 band=cv_quality.get("band", "unknown"),
#                 subscores=[
#                     SubscoreDTO(
#                         dimension=s.get("dimension", "unknown"),
#                         score=round(s.get("score", 0), 2),
#                         max_score=s.get("max_score", 0),
#                         evidence=s.get("evidence", []),
#                     )
#                     for s in cv_quality.get("subscores", [])
#                 ],
#             ),
#             jd_match=SectionScoreDTO(
#                 score=round(jd_match.get("overall_score", 0), 2),
#                 band=jd_match.get("band", "unknown"),
#                 subscores=[
#                     SubscoreDTO(
#                         dimension=s.get("dimension", "unknown"),
#                         score=round(s.get("score", 0), 2),
#                         max_score=s.get("max_score", 0),
#                         evidence=s.get("evidence", []),
#                     )
#                     for s in jd_match.get("subscores", [])
#                 ],
#             ),
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Fit Index scoring failed: {str(e)}")
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from cv_eval.engine import CVEvaluationEngine
from cv_eval.improvement import Improvement

router = APIRouter(
    prefix="/v1/cv",
)

# ---------- Init Engines ----------
evaluation_engine = CVEvaluationEngine()
improvement_engine = Improvement()

# ---------- Request DTOs ----------
class CVScoreRequest(BaseModel):
    cv_text: str = Field(..., description="Raw resume text")

class FitIndexRequest(BaseModel):
    cv_text: str = Field(..., description="Raw resume text")
    jd_text: str = Field(..., description="Raw job description text")
    include_constraints: bool = True

class ImprovementRequest(BaseModel):
    cv_text: str = Field(..., description="Raw resume text")
    jd_text: str = Field(..., description="Raw job description text")

# ---------- Routes ----------
@router.post("/score", summary="Score CV Quality (CV only)")
def score_cv(payload: CVScoreRequest):
    """
    Returns ONLY CV Quality scores (no JD match, no fit index).
    """
    try:
        result = evaluation_engine.evaluate(cv_text=payload.cv_text, jd_text="")
        return {"cv_quality": result.get("cv_quality", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV scoring failed: {str(e)}")


@router.post("/fit-index", summary="Score CV + JD (Fit Index)")
def score_fit_index(payload: FitIndexRequest):
    """
    Returns full evaluation (CV Quality + JD Match + Fit Index + Key Takeaways).
    """
    try:
        result = evaluation_engine.evaluate(
            cv_text=payload.cv_text,
            jd_text=payload.jd_text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fit Index scoring failed: {str(e)}")


@router.post("/improvement", summary="Generate CV Improvements")
def improve_cv(payload: ImprovementRequest):
    """
    Generates CV improvements:
    - Tailored Resume
    - Top 1% Candidate Benchmark
    - Cover Letter (under 200 words, returned last)
    """
    try:
        result = improvement_engine.evaluate(
            cv_text=payload.cv_text,
            jd_text=payload.jd_text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improvement generation failed: {str(e)}")
