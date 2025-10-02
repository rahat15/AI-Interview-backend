from typing import Dict, Any
from .graph import build_graph
from .evaluate.judge import summarize_scores


class InterviewSessionManager:
    """
    Manage interview sessions:
    - Tracks state (per user, per session)
    - Interfaces with LangGraph flow
    - Stores answers, evaluations, and reports
    """

    def __init__(self):
        # Structure: { user_id: { session_id: state } }
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.graphs: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        user_id: str,
        session_id: str,
        role_title: str,
        company_name: str,
        industry: str,
        jd: str,
        cv: str,
        round_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Initialize a new interview session and build its graph.
        """
        config = {
            "role_title": role_title,
            "company_name": company_name,
            "industry": industry,
            "round_type": round_type,
            "user_id": user_id,
            "session_id": session_id,
        }

        graph = build_graph(config=config, jd=jd, cv=cv)
        state = graph.get_state()  # initial compiled graph state

        # Ensure user exists
        if user_id not in self.sessions:
            self.sessions[user_id] = {}
            self.graphs[user_id] = {}

        self.sessions[user_id][session_id] = state
        self.graphs[user_id][session_id] = graph

        return state

    async def step(self, user_id: str, session_id: str, user_answer: str = None) -> Dict[str, Any]:
        """
        Advance one step in the interview flow.
        """
        if user_id not in self.graphs or session_id not in self.graphs[user_id]:
            raise ValueError("Session not found")

        graph = self.graphs[user_id][session_id]
        state = self.sessions[user_id][session_id]

        updated_state = await graph.step(state, user_answer=user_answer)
        self.sessions[user_id][session_id] = updated_state

        return updated_state

    def get_state(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Return current session state."""
        return self.sessions.get(user_id, {}).get(session_id, {})

    def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """Return all sessions for a user."""
        return self.sessions.get(user_id, {})

    def generate_report(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Generate a structured summary report for a specific session.
        """
        state = self.sessions.get(user_id, {}).get(session_id)
        if not state:
            return {"error": "Session not found"}

        evaluations = [h.get("evaluation") for h in state.get("history", []) if h.get("evaluation")]

        if not evaluations:
            return {"message": "No evaluations available yet."}

        summary = summarize_scores(evaluations)

        return {
            "user_id": user_id,
            "session_id": session_id,
            "role": state["config"]["role_title"],
            "company": state["config"]["company_name"],
            "industry": state["config"]["industry"],
            "avg_scores": summary,
            "history": state["history"],
        }


# Singleton manager
interview_manager = InterviewSessionManager()
