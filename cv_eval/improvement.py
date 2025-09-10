import logging
import json
from .llm_scorer import LLMScorer

logger = logging.getLogger(__name__)

class Improvement:
    """
    Generates improvements for CVs (LLM only, no fallback):
    - Tailored Resume highlights & rewording
    - Top 1% Candidate Benchmark
    - Cover Letter (under 200 words, returned last)
    """

    def __init__(self, model="llama-3.1-8b-instant"):
        try:
            self.llm = LLMScorer(model=model)
            logger.info("✅ Improvement LLM scorer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to init Improvement LLM scorer: {e}")
            raise

    def evaluate(self, cv_text: str, jd_text: str) -> dict:
        """
        Generate improvements for CV vs JD.
        Returns dict with:
        - tailored_resume
        - top_1_percent_gap
        - cover_letter
        """
        if not cv_text.strip() or not jd_text.strip():
            raise ValueError("Both CV text and JD text are required")

        result = self.llm.improvement(cv_text, jd_text)

        if not isinstance(result, dict):
            logger.error("❌ Groq LLM did not return a valid JSON dict")
            raise ValueError("Improvement LLM did not return valid JSON")

        return result

