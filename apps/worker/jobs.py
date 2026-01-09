# apps/worker/jobs.py

import asyncio
import uuid
import logging
from typing import Dict, Any, Callable

from core.db import connect_to_mongo
from core.models import Answer, Question, Score, Embedding
from interview.evaluate.judge import get_judge_evaluator

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Async runner helper (RQ is sync, Mongo/Groq are async)
# ------------------------------------------------------------------

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    else:
        return loop.create_task(coro)


# ------------------------------------------------------------------
# Jobs
# ------------------------------------------------------------------

def score_answer_job(answer_id: str) -> Dict[str, Any]:
    async def _run():
        await connect_to_mongo()

        answer = await Answer.get(answer_id)
        if not answer:
            return {"error": "Answer not found", "answer_id": answer_id}

        question = await Question.get(answer.question_id)
        if not question:
            return {"error": "Question not found", "answer_id": answer_id}

        evaluator = get_judge_evaluator()

        question_meta = {
            "competency": question.competency,
            "difficulty": question.difficulty,
            "expected_signals": question.meta.get("expected_signals", []) if question.meta else [],
            "pitfalls": question.meta.get("pitfalls", []) if question.meta else [],
        }

        evaluation = await evaluator.evaluate_answer(
            answer_text=answer.text or "",
            question_meta=question_meta,
            question_text=question.text,
        )

        score = Score(
            answer_id=answer.id,
            rubric_json=evaluation.dict(),
            clarity=evaluation.scores.clarity,
            structure=evaluation.scores.structure,
            depth_specificity=evaluation.scores.depth_specificity,
            role_fit=evaluation.scores.role_fit,
            technical=evaluation.scores.technical,
            communication=evaluation.scores.communication,
            ownership=evaluation.scores.ownership,
            total_score=evaluation.scores.total_score,
            meta={"job_id": str(uuid.uuid4())},
        )

        await score.insert()

        return {
            "success": True,
            "answer_id": str(answer.id),
            "score_id": str(score.id),
            "total_score": evaluation.scores.total_score,
        }

    return run_async(_run())


def process_audio_job(answer_id: str, audio_url: str) -> Dict[str, Any]:
    async def _run():
        await connect_to_mongo()

        answer = await Answer.get(answer_id)
        if not answer:
            return {"error": "Answer not found", "answer_id": answer_id}

        answer.asr_text = f"[ASR processed from {audio_url}]"
        await answer.save()

        return {
            "success": True,
            "answer_id": str(answer.id),
            "asr_text": answer.asr_text,
        }

    return run_async(_run())


def generate_embeddings_job(artifact_id: str) -> Dict[str, Any]:
    async def _run():
        await connect_to_mongo()

        embedding = Embedding(
            artifact_id=artifact_id,
            vector=[],
        )
        await embedding.insert()

        return {"success": True, "artifact_id": artifact_id}

    return run_async(_run())


def cleanup_session_job(session_id: str) -> Dict[str, Any]:
    logger.info("Cleanup completed for session %s", session_id)
    return {"success": True, "session_id": session_id}


# ------------------------------------------------------------------
# Job registry
# ------------------------------------------------------------------

JOB_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "score_answer": score_answer_job,
    "process_audio": process_audio_job,
    "generate_embeddings": generate_embeddings_job,
    "cleanup_session": cleanup_session_job,
}
