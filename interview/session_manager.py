import uuid
import json
import redis
from apps.interview.graph import build_dynamic_graph
from apps.interview.question import generate_question
from apps.interview.evaluate.judge import evaluate_answer
from apps.interview.evaluate.judge import summarize_scores
from apps.interview.followup import should_followup

class InterviewSessionManager:
    def __init__(self):
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)

    async def create_session(self, cv, jd, config):
        cv_text = (await cv.read()).decode("utf-8")
        jd_text = (await jd.read()).decode("utf-8")

        session_id = str(uuid.uuid4())
        state = {
            "cv": cv_text,
            "jd": jd_text,
            "config": config,
            "history": [],
            "scores": [],
            "stage": None
        }

        self.redis.set(session_id, json.dumps(state))

        # Build graph (compiled JSON)
        graph = build_dynamic_graph(config)
        self.redis.set(f"{session_id}_graph", json.dumps({"graph": "compiled"}))

        # Ask first question
        first_question = await generate_question(state, stage=config["level"])
        state["stage"] = config["level"]
        self.redis.set(session_id, json.dumps(state))

        return session_id, first_question

    async def process_answer(self, session_id: str, user_answer: str):
        state = json.loads(self.redis.get(session_id))

        state["history"].append({"q": "last_q", "a": user_answer})

        # Evaluate
        eval_result = await evaluate_answer(user_answer, state["jd"], state["cv"])
        state["scores"].append(eval_result)

        # Follow-up check
        if should_followup(eval_result):
            next_q = await generate_question(state, stage=state["stage"], followup=True)
        else:
            next_q = await generate_question(state, stage=state["config"]["level"])

        self.redis.set(session_id, json.dumps(state))
        return next_q, eval_result

    async def finalize(self, session_id: str):
        state = json.loads(self.redis.get(session_id))
        report = summarize_scores(state["scores"])
        return report
