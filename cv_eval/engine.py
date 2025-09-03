# import logging
# from datetime import datetime

# from .schemas import (
#     CVEvaluationRequest,
#     CVEvaluationResult,
#     EvaluationResult,
#     ConstraintsDisclosure,
#     KeyTakeaways,
# )
# from .llm_scorer import LLMScorer
# from . import heuristics

# logger = logging.getLogger(__name__)


# class CVEvaluationEngine:
#     """Main entrypoint: evaluates CV vs JD using LLM (preferred) with heuristics fallback."""

#     def __init__(self, use_llm: bool = True):
#         self.use_llm = use_llm
#         self.llm = None
#         if self.use_llm:
#             try:
#                 self.llm = LLMScorer()
#                 logger.info("LLM scorer initialized successfully")
#             except Exception as e:
#                 logger.warning(f"LLM scorer failed to initialize: {e}. Falling back to heuristics.")
#                 self.use_llm = False

#     def evaluate(self, req: CVEvaluationRequest) -> EvaluationResult:
#         """Unified evaluation. Returns EvaluationResult (preferred schema)."""

#         if self.use_llm and self.llm:
#             try:
#                 logger.info("Running evaluation with LLM scorer")
#                 return self.llm.evaluate(req.cv_text, req.jd_text)
#             except Exception as e:
#                 logger.warning(f"LLM evaluation failed: {e}. Falling back to heuristics.")

#         # -------------------------
#         # Heuristic Fallback Path
#         # -------------------------
#         logger.info("Using heuristic scoring")

#         cv_quality = heuristics.score_cv_quality(req.cv_text)
#         jd_match = heuristics.score_jd_match(req.cv_text, req.jd_text)

#         # Fit index: weighted combination
#         fit_index = round(0.6 * jd_match.overall_score + 0.4 * cv_quality.overall_score, 2)
#         band = heuristics._band(fit_index)

#         constraints_disclosure = ConstraintsDisclosure(
#             location_match=True,
#             work_authorization=True,
#             remote_work=True,
#             travel_requirements=True,
#             constraints_score=10.0,
#             constraints_evidence=["Default heuristic: assumed no constraints"]
#         )

#         # Build old CVEvaluationResult
#         legacy = CVEvaluationResult(
#             cv_quality=cv_quality,
#             jd_match=jd_match,
#             fit_index=fit_index,
#             band=band,
#             constraints_disclosure=constraints_disclosure,
#             evaluation_timestamp=datetime.utcnow(),
#             meta={"evaluator": {"provider": "heuristics"}}
#         )

#         # Convert legacy → unified EvaluationResult
#         return EvaluationResult(
#             cv_quality=legacy.cv_quality,
#             job_match=legacy.jd_match,   # 🔄 rename
#             key_takeaways=KeyTakeaways(
#                 red_flags=[],
#                 green_flags=["Heuristic evaluation completed"]
#             ),
#             evaluation_timestamp=legacy.evaluation_timestamp,
#             meta=legacy.meta
#         )


from .llm_scorer import LLMScorer
import logging
from . import heuristics  # fallback

logger = logging.getLogger(__name__)

class CVEvaluationEngine:
    def __init__(self, model="llama-3.1-8b-instant", use_llm=True):
        self.use_llm = use_llm
        self.llm = None
        if self.use_llm:
            try:
                self.llm = LLMScorer(model=model)
                logger.info("✅ LLM scorer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to init LLM scorer: {e}")
                self.use_llm = False  # allow heuristics fallback

    def evaluate(self, cv_text: str, jd_text: str = "") -> dict:
        """
        Evaluate CV or CV+JD.
        - Prefer LLM for all cases
        - If LLM fails, fallback to heuristics
        """
        if not cv_text.strip():
            raise ValueError("CV text cannot be empty")

        # ----------------
        # Try LLM first
        # ----------------
        if self.use_llm and self.llm:
            try:
                if jd_text and jd_text.strip():
                    # CV + JD evaluation
                    return self.llm.unified_evaluate(cv_text, jd_text)
                else:
                    # CV-only evaluation
                    return {"cv_quality": self.llm.score_cv_only(cv_text)}
            except Exception as e:
                logger.error(f"❌ LLM evaluation failed: {e}. Falling back to heuristics...")

        # ----------------
        # Heuristic fallback
        # ----------------
        logger.warning("⚠️ Using heuristics fallback")

        result = {
            "cv_quality": heuristics.score_cv_quality(cv_text)
        }

        if jd_text and jd_text.strip():
            jd_match = heuristics.score_jd_match(cv_text, jd_text)
            result["jd_match"] = jd_match
            result["fit_index"] = round(
                0.6 * jd_match["overall_score"] + 0.4 * result["cv_quality"]["overall_score"], 2
            )
            result["band"] = heuristics._band(result["fit_index"])

        return result
