from typing import Dict, Any
import asyncio
import logging

from interview.graph import build_graph
from interview.evaluate.judge import summarize_scores

logger = logging.getLogger(__name__)


class InterviewSessionManager:
    """
    Orchestrates interview sessions using LangGraph.
    Keeps state per user_id + session_id.
    """

    def __init__(self):
        # In-memory storage (can replace with Redis/DB later)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.graphs: Dict[str, Any] = {}

    def _make_key(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def create_session(
        self,
        user_id: str,
        session_id: str,
        role_title: str,
        company_name: str,
        industry: str,
        jd: str,
        cv: str,
        round_type: str = "full",
    ) -> Dict[str, Any]:
        """
        Initialize a new interview session and its LangGraph.
        """

        key = self._make_key(user_id, session_id)

        # Config that nodes / prompts can use
        config = {
            "user_id": user_id,
            "session_id": session_id,
            "role_title": role_title,
            "company_name": company_name,
            "industry": industry,
            "jd": jd,
            "cv": cv,
            "round_type": round_type,
        }

        # Build compiled graph for this session
        graph = build_graph(config)

        # Initial state passed into the graph
        state: Dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "stage": "intro",
            "history": [],
            "should_follow_up": False,
            "completed": False,
            "config": config,
            "jd": jd,
            "cv": cv,
        }

        self.sessions[key] = state
        self.graphs[key] = graph
        return state

    async def step(
        self,
        user_id: str,
        session_id: str,
        user_answer: str | None = None,
    ) -> Dict[str, Any]:
        """
        Advance the graph by one step.

        IMPORTANT:
        - Do NOT pass config= into the compiled graph.
        - Just pass the state dict. LangGraph handles config internally.
        """

        key = self._make_key(user_id, session_id)
        if key not in self.sessions:
            raise ValueError("Session not found")

        state = self.sessions[key]
        graph = self.graphs[key]

        # Attach answer if provided
        if user_answer and state.get("history"):
            state["history"][-1]["answer"] = user_answer

        logger.info("▶️ Running LangGraph step for user=%s, session=%s", user_id, session_id)

        try:
            # Async compiled graph (preferred)
            if hasattr(graph, "ainvoke") and callable(graph.ainvoke):
                new_state = await graph.ainvoke(state)

            # Sync compiled graph
            elif hasattr(graph, "invoke") and callable(graph.invoke):
                new_state = graph.invoke(state)

            # Raw async callable
            elif asyncio.iscoroutinefunction(graph):
                new_state = await graph(state)

            # Raw sync callable
            elif callable(graph):
                new_state = graph(state)

            else:
                raise RuntimeError("Unsupported graph invocation type")

        except Exception:
            logger.exception("❌ Error while invoking LangGraph")
            raise

        self.sessions[key] = new_state
        return new_state

    def get_state(self, user_id: str, session_id: str) -> Dict[str, Any] | None:
        return self.sessions.get(self._make_key(user_id, session_id))

    def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        prefix = f"{user_id}:"
        return {
            sid.split(":", 1)[1]: state
            for sid, state in self.sessions.items()
            if sid.startswith(prefix)
        }

    def generate_report(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Aggregate all evaluations for a session and produce a summary.
        Uses summarize_scores() from evaluate/judge.py.
        """
        state = self.get_state(user_id, session_id)
        if not state:
            return {"error": "Session not found"}

        evaluations = [
            h["evaluation"]
            for h in state.get("history", [])
            if h.get("evaluation")
        ]
        if not evaluations:
            return {"error": "No evaluations available"}

        avg_scores = summarize_scores(evaluations)

        return {
            "session_id": session_id,
            "user_id": user_id,
            "role": state["config"]["role_title"],
            "company": state["config"]["company_name"],
            "industry": state["config"]["industry"],
            "avg_scores": avg_scores,
            "history": state["history"],
        }


# Singleton instance
interview_manager = InterviewSessionManager()
