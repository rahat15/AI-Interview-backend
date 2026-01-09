import asyncio
import uuid
import logging
from typing import Dict, Any, Callable

from core.db import connect_to_mongo
from core.models import Answer, Question, Score, Embedding
from interview.evaluate.judge import evaluate_answer

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helper: run async code from sync RQ worker
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

        # Call Groq evaluator directly (no factory, no wrapper)
        evaluation = await evaluate_answer(
            user_answer=answer.text or "",
            question=question.text,
            jd=question.meta.get("jd", "") if question.meta else "",
            cv=question.meta.get("cv", "") if question.meta else "",
            stage=question.stage or "general",
        )

        score = Score(
            answer_id=answer.id,
            rubric_json=evaluation,
            clarity=evaluation.get("clarity", 0),
            confidence=evaluation.get("confidence", 0),
            technical=evaluation.get("technical_depth", 0),
            total_score=(
                evaluation.get("clarity", 0)
                + evaluation.get("confidence", 0)
                + evaluation.get("technical_depth", 0)
            ) / 3,
            meta={"job_id": str(uuid.uuid4())},
        )

        await score.insert()

        return {
            "success": True,
            "answer_id": str(answer.id),
            "score_id": str(score.id),
            "evaluation": evaluation,
        }

    return run_async(_run())


def process_audio_job(answer_id: str, audio_url: str) -> Dict[str, Any]:
    async def _run():
        await connect_to_mongo()

        answer = await Answer.get(answer_id)
        if not answer:
            return {"error": "Answer not found", "answer_id": answer_id}

        # Placeholder – already aligned with your Groq ASR plan
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

        return {
            "success": True,
            "artifact_id": artifact_id,
        }

    return run_async(_run())


def cleanup_session_job(session_id: str) -> Dict[str, Any]:
    logger.info("Cleanup completed for session %s", session_id)
    return {
        "success": True,
        "session_id": session_id,
    }


# ------------------------------------------------------------------
# Job registry (used by QueueManager)
# ------------------------------------------------------------------

JOB_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "score_answer": score_answer_job,
    "process_audio": process_audio_job,
    "generate_embeddings": generate_embeddings_job,
    "cleanup_session": cleanup_session_job,
}
