from typing import Dict, Any
from interview.graph import build_graph
import asyncio


class InterviewSessionManager:
    """
    Orchestrates interview sessions using LangGraph.
    Keeps state per user_id + session_id.
    """

    def __init__(self):
        # In-memory storage (can replace with Redis/Postgres later)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.graphs: Dict[str, Any] = {}  # compiled LangGraph per session

    def _make_key(self, user_id: str, session_id: str) -> str:
        """Unique key for each user+session pair."""
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
        """Initialize a new interview session and graph."""

        key = self._make_key(user_id, session_id)

        # Build config dict
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

        # Create LangGraph for this session
        graph = build_graph(config)

        # Initialize state
        state = {
            "session_id": session_id,
            "user_id": user_id,
            "stage": "intro",
            "history": [],
            "should_follow_up": False,
            "completed": False,
            "config": config,
        }

        self.sessions[key] = state
        self.graphs[key] = graph
        return state

    async def step(self, user_id: str, session_id: str, user_answer: str = None) -> Dict[str, Any]:
        """
        Advance the graph by one step.
        If `user_answer` is provided, attach it before stepping.
        """
        key = self._make_key(user_id, session_id)
        if key not in self.sessions:
            raise ValueError("Session not found")

        state = self.sessions[key]
        graph = self.graphs[key]

        # Attach answer if provided
        if user_answer and state.get("history"):
            state["history"][-1]["answer"] = user_answer

        # Run one step in the graph
        if asyncio.iscoroutinefunction(graph):
            new_state = await graph(state)
        else:
            new_state = graph.invoke(state)

        # Save updated state
        self.sessions[key] = new_state
        return new_state

    def get_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Return current state of a session."""
        return self.sessions.get(self._make_key(user_id, session_id))

    def get_user_sessions(self, user_id: str):
        """List all sessions for a given user."""
        return {
            sid.split(":")[1]: state
            for sid, state in self.sessions.items()
            if sid.startswith(f"{user_id}:")
        }

    def generate_report(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Aggregate evaluations into a report."""
        state = self.get_state(user_id, session_id)
        if not state:
            return {"error": "Session not found"}

        evaluations = [h.get("evaluation") for h in state.get("history", []) if h.get("evaluation")]
        if not evaluations:
            return {"error": "No evaluations available"}

        # Compute averages
        totals = {"technical_depth": 0, "relevance": 0, "communication": 0, "behavioral": 0}
        for ev in evaluations:
            for k in totals:
                totals[k] += ev.get(k, 0)

        avg_scores = {k: round(v / len(evaluations), 2) for k, v in totals.items()}
        overall_score = sum(avg_scores.values()) / len(avg_scores)

        if overall_score >= 8.5:
            overall = "Strong Hire"
        elif overall_score >= 7:
            overall = "Hire"
        elif overall_score >= 5:
            overall = "Weak Hire"
        else:
            overall = "No Hire"

        return {
            "session_id": session_id,
            "user_id": user_id,
            "role": state["config"]["role_title"],
            "company": state["config"]["company_name"],
            "industry": state["config"]["industry"],
            "avg_scores": {**avg_scores, "overall": overall},
            "history": state["history"],
        }


# Singleton instance
interview_manager = InterviewSessionManager()
