# # import os, json, time, logging
# # from typing import Dict, Any, Optional, List
# # from pydantic import ValidationError

# # from .schemas import EvaluationResult, ScoreResult, SubScore, KeyTakeaways
# # from .prompts import UNIFIED_EVALUATION_PROMPT

# # from dotenv import load_dotenv
# # import os

# # # Load variables from .env into environment
# # load_dotenv()

# # logger = logging.getLogger(__name__)

# # try:
# #     from groq import Groq as _Groq
# # except ImportError:
# #     _Groq = None


# # class LLMScorerError(Exception):
# #     pass


# # class LLMScorer:
# #     """Unified LLM scorer for CV + JD evaluation."""

# #     def __init__(self, model: Optional[str] = None, temperature: float = 0.0, timeout: int = 60):
# #         self.temperature = temperature
# #         self.timeout = timeout
# #         self.model = model or os.getenv("LLM_MODEL", "llama3-8b-8192")

# #         if not _Groq:
# #             raise ImportError("groq client not installed. Run: pip install groq")
# #         if not os.getenv("GROQ_API_KEY"):
# #             raise ValueError("GROQ_API_KEY environment variable not set")

# #         self.client = _Groq()

# #     # ---------- Unified entry point ----------
# #     def evaluate(self, cv_text: str, jd_text: str) -> EvaluationResult:
# #         """Run unified prompt and parse JSON into EvaluationResult"""
# #         prompt = UNIFIED_EVALUATION_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
# #         raw = self._call_llm(prompt)
# #         parsed = self._parse_llm_response(raw)

# #         return EvaluationResult(**parsed)

# #     # ---------- LLM call ----------
# #     def _call_llm(self, prompt: str) -> str:
# #         for attempt in range(3):
# #             try:
# #                 resp = self.client.chat.completions.create(
# #                     model=self.model,
# #                     messages=[
# #                         {"role": "system", "content": "You are a strict JSON generator."},
# #                         {"role": "user", "content": prompt},
# #                     ],
# #                     temperature=self.temperature,
# #                     max_tokens=4000,
# #                     timeout=self.timeout,
# #                 )
# #                 return resp.choices[0].message.content.strip()
# #             except Exception as e:
# #                 logger.error(f"[Groq] API call failed (attempt {attempt+1}/3): {e}")
# #                 if attempt == 2:
# #                     raise LLMScorerError(f"Groq API call failed: {e}")
# #                 time.sleep(1.5 ** attempt)

# #     # ---------- JSON parsing ----------
# #     def _parse_llm_response(self, response: str) -> Dict[str, Any]:
# #         text = self._extract_json(response)
# #         try:
# #             return json.loads(text)
# #         except Exception as e:
# #             raise LLMScorerError(f"Failed to parse LLM JSON: {e}\n{text}")

# #     @staticmethod
# #     def _extract_json(text: str) -> str:
# #         if "```json" in text:
# #             s = text.find("```json") + 7
# #             e = text.find("```", s)
# #             return text[s:e].strip()
# #         elif "```" in text:
# #             s = text.find("```") + 3
# #             e = text.find("```", s)
# #             return text[s:e].strip()
# #         return text[text.find("{"): text.rfind("}")+1]


    
# #     def unified_evaluate(self, cv_text: str, jd_text: str) -> EvaluationResult:
# #         """Run unified evaluation prompt and return EvaluationResult."""
# #         prompt = UNIFIED_EVALUATION_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
# #         raw = self._call_llm(prompt)
# #         cleaned = self._extract_json_from_response(raw)

# #         try:
# #             data = json.loads(cleaned)
# #         except json.JSONDecodeError as e:
# #             logger.error(f"Failed to parse JSON from LLM: {e}")
# #             raise

# #         # 🔑 Build Pydantic model directly from dict
# #         return EvaluationResult(**data)


# import json, time, logging
# from .prompts import UNIFIED_EVALUATION_PROMPT

# logger = logging.getLogger(__name__)


# from dotenv import load_dotenv
# import os

# # Load variables from .env into environment
# load_dotenv()


# class LLMScorer:
#     def __init__(self, client=None, model="llama3-8b-8192", temperature=0.0, timeout=60):
#         from groq import Groq
#         self.client = client or Groq()
#         self.model = model
#         self.temperature = temperature
#         self.timeout = timeout

#     def unified_evaluate(self, cv_text: str, jd_text: str) -> dict:
#         """Return raw JSON dict (no schema validation)."""
#         prompt = UNIFIED_EVALUATION_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
#         raw = self._call_llm(prompt)
#         cleaned = self._extract_json_from_response(raw)

#         try:
#             return json.loads(cleaned)   # 👈 just return dict
#         except json.JSONDecodeError as e:
#             logger.error(f"Could not parse JSON: {e}")
#             raise

#     def _call_llm(self, prompt: str) -> str:
#         for attempt in range(3):
#             try:
#                 resp = self.client.chat.completions.create(
#                     model=self.model,
#                     messages=[
#                         {"role": "system", "content": "You are a strict JSON generator."},
#                         {"role": "user", "content": prompt},
#                     ],
#                     temperature=self.temperature,
#                     max_tokens=3500,
#                 )
#                 return resp.choices[0].message.content.strip()
#             except Exception as e:
#                 logger.error(f"Groq API call failed (attempt {attempt+1}/3): {e}")
#                 if attempt == 2:
#                     raise
#                 time.sleep(1.5 ** attempt)

#     @staticmethod
#     def _extract_json_from_response(text: str) -> str:
#         if "```json" in text:
#             s = text.find("```json") + 7
#             e = text.find("```", s)
#             return text[s:e].strip()
#         elif "```" in text:
#             s = text.find("```") + 3
#             e = text.find("```", s)
#             return text[s:e].strip()
#         # fallback
#         start, end = text.find("{"), text.rfind("}")
#         return text[start:end+1] if start != -1 and end != -1 else text
# import os, json, time, logging
# from typing import Dict, Any, Optional, List
# from pydantic import ValidationError

# from .schemas import EvaluationResult, ScoreResult, SubScore, KeyTakeaways
# from .prompts import UNIFIED_EVALUATION_PROMPT

# from dotenv import load_dotenv
# import os

# # Load variables from .env into environment
# load_dotenv()

# logger = logging.getLogger(__name__)

# try:
#     from groq import Groq as _Groq
# except ImportError:
#     _Groq = None


# class LLMScorerError(Exception):
#     pass


# class LLMScorer:
#     """Unified LLM scorer for CV + JD evaluation."""

#     def __init__(self, model: Optional[str] = None, temperature: float = 0.0, timeout: int = 60):
#         self.temperature = temperature
#         self.timeout = timeout
#         self.model = model or os.getenv("LLM_MODEL", "llama3-8b-8192")

#         if not _Groq:
#             raise ImportError("groq client not installed. Run: pip install groq")
#         if not os.getenv("GROQ_API_KEY"):
#             raise ValueError("GROQ_API_KEY environment variable not set")

#         self.client = _Groq()

#     # ---------- Unified entry point ----------
#     def evaluate(self, cv_text: str, jd_text: str) -> EvaluationResult:
#         """Run unified prompt and parse JSON into EvaluationResult"""
#         prompt = UNIFIED_EVALUATION_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
#         raw = self._call_llm(prompt)
#         parsed = self._parse_llm_response(raw)

#         return EvaluationResult(**parsed)

#     # ---------- LLM call ----------
#     def _call_llm(self, prompt: str) -> str:
#         for attempt in range(3):
#             try:
#                 resp = self.client.chat.completions.create(
#                     model=self.model,
#                     messages=[
#                         {"role": "system", "content": "You are a strict JSON generator."},
#                         {"role": "user", "content": prompt},
#                     ],
#                     temperature=self.temperature,
#                     max_tokens=4000,
#                     timeout=self.timeout,
#                 )
#                 return resp.choices[0].message.content.strip()
#             except Exception as e:
#                 logger.error(f"[Groq] API call failed (attempt {attempt+1}/3): {e}")
#                 if attempt == 2:
#                     raise LLMScorerError(f"Groq API call failed: {e}")
#                 time.sleep(1.5 ** attempt)

#     # ---------- JSON parsing ----------
#     def _parse_llm_response(self, response: str) -> Dict[str, Any]:
#         text = self._extract_json(response)
#         try:
#             return json.loads(text)
#         except Exception as e:
#             raise LLMScorerError(f"Failed to parse LLM JSON: {e}\n{text}")

#     @staticmethod
#     def _extract_json(text: str) -> str:
#         if "```json" in text:
#             s = text.find("```json") + 7
#             e = text.find("```", s)
#             return text[s:e].strip()
#         elif "```" in text:
#             s = text.find("```") + 3
#             e = text.find("```", s)
#             return text[s:e].strip()
#         return text[text.find("{"): text.rfind("}")+1]


    
#     def unified_evaluate(self, cv_text: str, jd_text: str) -> EvaluationResult:
#         """Run unified evaluation prompt and return EvaluationResult."""
#         prompt = UNIFIED_EVALUATION_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
#         raw = self._call_llm(prompt)
#         cleaned = self._extract_json_from_response(raw)

#         try:
#             data = json.loads(cleaned)
#         except json.JSONDecodeError as e:
#             logger.error(f"Failed to parse JSON from LLM: {e}")
#             raise

#         # 🔑 Build Pydantic model directly from dict
#         return EvaluationResult(**data)

# cv_eval/llm_scorer.py


import json, time, logging, os
from dotenv import load_dotenv
from .prompts import UNIFIED_EVALUATION_PROMPT, CV_ONLY_EVALUATION_PROMPT, IMPROVEMENT_PROMPT, GENERAL_IMPROVEMENT_PROMPT, RESUME_REWRITE_PROMPT


load_dotenv()
logger = logging.getLogger(__name__)

class LLMScorer:
    def __init__(self, client=None, model="llama-3.1-8b-instant", temperature=0.0, timeout=60):
        from groq import Groq
        self.client = client or Groq()
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    # ---------- CV vs JD (auto-switch) ----------
    def unified_evaluate(self, cv_text: str, jd_text: str = "") -> dict:
        if jd_text and jd_text.strip():
            prompt = UNIFIED_EVALUATION_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
        else:
            prompt = CV_ONLY_EVALUATION_PROMPT.format(cv_text=cv_text)

        return self._generate_and_parse_json(prompt)

    # ---------- CV only (legacy alias) ----------
    def evaluate_cv_only(self, cv_text: str) -> dict:
        return self.unified_evaluate(cv_text=cv_text, jd_text="")

    # ---------- Internals ----------
    def _generate_and_parse_json(self, prompt: str) -> dict:
        """Retry LLM call if JSON parsing fails."""
        for attempt in range(3):
            try:
                raw = self._call_llm(prompt)
                cleaned = self._extract_json_from_response(raw)
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed (attempt {attempt+1}/3): {e}. Retrying.")
                if attempt == 2:
                    logger.error(f"Final JSON parsing failure. Raw response: {raw}")
                    raise
        raise ValueError("Failed to generate valid JSON")

    def _call_llm(self, prompt: str) -> str:
        for attempt in range(3):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a strict JSON generator."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=3500,
                    response_format={"type": "json_object"},
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Groq API call failed (attempt {attempt+1}/3): {e}")
                if attempt == 2:
                    raise
                time.sleep(1.5 ** attempt)
    
    def improvement(self, cv_text: str, jd_text: str = "") -> dict:
        if not cv_text.strip():
            raise ValueError("CV text is required for improvement")

        if jd_text and jd_text.strip():
            prompt = IMPROVEMENT_PROMPT.format(cv_text=cv_text, jd_text=jd_text)
        else:
            prompt = GENERAL_IMPROVEMENT_PROMPT.format(cv_text=cv_text)
            
        return self._generate_and_parse_json(prompt)

    def rewrite_resume(self, cv_text: str, improvement_context: str) -> dict:
        if not cv_text.strip():
            raise ValueError("CV text is required")
        
        prompt = RESUME_REWRITE_PROMPT.format(
            cv_text=cv_text, 
            improvement_context=improvement_context or "No specific improvements requested. Just structure the CV."
        )
        return self._generate_and_parse_json(prompt)


    @staticmethod
    def _extract_json_from_response(text: str) -> str:
        if "```json" in text:
            s = text.find("```json") + 7
            e = text.find("```", s)
            return text[s:e].strip()
        elif "```" in text:
            s = text.find("```") + 3
            e = text.find("```", s)
            return text[s:e].strip()
        start, end = text.find("{"), text.rfind("}")
        return text[start:end+1] if start != -1 and end != -1 else text
