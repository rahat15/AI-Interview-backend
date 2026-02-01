from .llm_scorer import LLMScorer
import logging

logger = logging.getLogger(__name__)

class Improvement:
    def __init__(self):
        self.llm_scorer = LLMScorer()
    
    def evaluate(self, cv_text: str, jd_text: str = ""):
        """Generate CV improvements using LLM"""
        try:
            return self.llm_scorer.improvement(cv_text, jd_text)
        except Exception as e:
            logger.error(f"LLM improvement failed: {e}")
            return self._error_response()

    def rewrite_resume(self, cv_text: str, improvement_context: str) -> dict:
        """Rewrite resume based on improvements"""
        try:
            return self.llm_scorer.rewrite_resume(cv_text, improvement_context)
        except Exception as e:
            logger.error(f"Resume rewrite failed: {e}")
            raise e

    def _error_response(self):
         return {
                "tailored_resume": {
                    "summary": "Error generating improvements",
                    "experience": [],
                    "skills": [],
                    "projects": []
                },
                "top_1_percent_gap": {
                    "strengths": [],
                    "gaps": [],
                    "actionable_next_steps": []
                },
                "cover_letter": "Error generating cover letter"
            }