from typing import Dict, Any, List
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import should_followup

class InterviewSessionManager:
    """
    Manage interview sessions:
    - Tracks state
    - Generates questions
    - Stores answers
    - Triggers evaluations & follow-ups
    """

    def __init__(self):
        # store sessions in memory (Redis/Postgres later)
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        session_id: str,
        role_title: str,
        company_name: str,
        industry: str,
        jd: str,
        cv: str,
        stage: str = "intro"
    ) -> Dict[str, Any]:
        """Initialize a new interview session."""
        state = {
            "session_id": session_id,
            "config": {
                "role_title": role_title,
                "company_name": company_name,
                "industry": industry,
            },
            "jd": jd,
            "cv": cv,
            "stage": stage,
            "history": [],       # list of {q, a, eval}
            "should_follow_up": False,
            "completed": False,
        }
        self.sessions[session_id] = state
        return state

    async def get_next_question(self, session_id: str) -> str:
        """Get the next question (or follow-up if needed)."""
        state = self.sessions[session_id]

        q = await generate_question(
            state=state,
            stage=state.get("stage", "intro"),
            followup=state.get("should_follow_up", False)
        )

        # store placeholder in history
        state["history"].append({"q": q, "a": None, "eval": None})
        self.sessions[session_id] = state
        return q

    async def submit_answer(self, session_id: str, answer_text: str) -> Dict[str, Any]:
        """Submit an answer, run evaluation, and decide follow-up."""
        state = self.sessions[session_id]
        history = state["history"]

        if not history:
            raise ValueError("No question has been asked yet.")

        # attach answer
        history[-1]["a"] = answer_text

        # evaluate answer
        eval_result = await evaluate_answer(
            user_answer=answer_text,
            jd=state["jd"],
            cv=state["cv"]
        )
        history[-1]["eval"] = eval_result

        # decide follow-up
        state["should_follow_up"] = should_followup(eval_result)

        self.sessions[session_id] = state
        return eval_result

    def advance_stage(self, session_id: str, new_stage: str) -> Dict[str, Any]:
        """Manually move to the next stage (e.g., from intro → technical)."""
        state = self.sessions[session_id]
        state["stage"] = new_stage
        state["should_follow_up"] = False
        self.sessions[session_id] = state
        return state

    def get_state(self, session_id: str) -> Dict[str, Any]:
        """Return current session state."""
        return self.sessions[session_id]

    def generate_report(self, session_id: str) -> Dict[str, Any]:
        """Generate a summary report after interview is complete."""
        state = self.sessions[session_id]
        evaluations = [h["eval"] for h in state["history"] if h.get("eval")]

        if not evaluations:
            return {"message": "No evaluations available yet."}

        # simple averages for now
        avg_scores = {
            "technical_depth": sum(e.get("technical_depth", 0) for e in evaluations) / len(evaluations),
            "relevance": sum(e.get("relevance", 0) for e in evaluations) / len(evaluations),
            "communication": sum(e.get("communication", 0) for e in evaluations) / len(evaluations),
            "behavioral": sum(e.get("behavioral", 0) for e in evaluations) / len(evaluations),
        }

        return {
            "session_id": session_id,
            "role": state["config"]["role_title"],
            "company": state["config"]["company_name"],
            "industry": state["config"]["industry"],
            "stages_covered": list({h.get("stage", state["stage"]) for h in state["history"]}),
            "avg_scores": avg_scores,
            "history": state["history"]
        }


# singleton manager
interview_manager = InterviewSessionManager()
