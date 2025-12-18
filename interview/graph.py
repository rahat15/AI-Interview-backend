from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal, Any

from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision
from interview.stages import get_stage_order, get_max_questions

# ---------------------------
# State Definitions
# ---------------------------

class InterviewHistoryItem(TypedDict):
    question: str
    answer: str | None
    evaluation: dict | None
    stage: str
    is_followup: bool


class InterviewState(TypedDict):
    stage: Literal["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    session_config: dict
    history: List[InterviewHistoryItem]
    should_follow_up: bool
    completed: bool


# ---------------------------
# Graph Nodes
# ---------------------------

async def ask_question(state: InterviewState, **kwargs) -> InterviewState:
    """Generate and append a question."""
    stage = state["stage"]
    followup = state.get("should_follow_up", False)

    # generate_question handles JD/CV from session_config
    q = await generate_question(state, stage, followup)

    state["history"].append({
        "question": q,
        "answer": None,
        "evaluation": None,
        "stage": stage,
        "is_followup": followup,  # ✅ persisted for follow-up counting
    })

    # Reset follow-up flag after asking
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState, **kwargs) -> InterviewState:
    """Evaluate candidate's answer."""
    if not state["history"]:
        return state

    last = state["history"][-1]

    # No answer yet
    if not last.get("answer"):
        return state

    try:
        evaluation = await evaluate_answer(
            user_answer=last["answer"],
            question=last["question"],
            jd=state["session_config"].get("jd", ""),
            cv=state["session_config"].get("cv", ""),
            stage=state["stage"],
        )
        last["evaluation"] = evaluation
    except Exception as e:
        print(f"Evaluation error: {e}")
        last["evaluation"] = {
            "summary": "Evaluation skipped due to error.",
            "clarity": 0,
            "confidence": 0,
            "technical_depth": 0,
        }

    return state


async def decide_followup_node(state: InterviewState, **kwargs) -> InterviewState:
    """Decide whether to follow up or move to the next stage."""

    # Optional: extra guard to prevent pathological loops (keep if you want)
    history = state.get("history", [])
    consecutive_followups = 0
    if history:
        for item in reversed(history):
            if item.get("is_followup", False):
                consecutive_followups += 1
            else:
                break

    # Hard stop (graph-level) — your followup.py already enforces stage-based limits
    if consecutive_followups >= 4:
        state["should_follow_up"] = False
        return state

    decision = await followup_decision(state)
    state["should_follow_up"] = (decision.get("decision") == "followup")
    return state


def stage_transition_node(state: InterviewState, **kwargs) -> InterviewState:
    """Transition to next stage based on stages.py configuration."""
    if state.get("should_follow_up"):
        return state

    config = state.get("session_config", {})
    round_type = config.get("round_type", "full")
    current_stage = state["stage"]

    history = state.get("history", [])

    # Count only main questions (not follow-ups)
    current_stage_count = sum(
        1 for h in history
        if h.get("stage") == current_stage and not h.get("is_followup", False)
    )

    limit = get_max_questions(round_type, current_stage)

    if current_stage_count >= limit:
        order = get_stage_order(round_type)
        try:
            curr_idx = order.index(current_stage)
            if curr_idx + 1 < len(order):
                state["stage"] = order[curr_idx + 1]
            else:
                state["completed"] = True
        except ValueError:
            state["completed"] = True

    return state


# ---------------------------
# Routing Logic
# ---------------------------

def route_start(state: InterviewState):
    """Determine entry point based on history."""
    if not state.get("history"):
        return "ask_question"
    return "evaluate_answer"


def check_done(state: InterviewState):
    """Check if interview is completed."""
    if state.get("completed"):
        return END
    return "ask_question"


# ---------------------------
# Graph Builder
# ---------------------------

def build_graph(config: dict) -> Any:
    g = StateGraph(InterviewState)

    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    g.add_node("decide_followup", decide_followup_node)
    g.add_node("stage_transition", stage_transition_node)

    g.set_conditional_entry_point(
        route_start,
        {
            "ask_question": "ask_question",
            "evaluate_answer": "evaluate_answer",
        }
    )

    g.add_edge("ask_question", END)
    g.add_edge("evaluate_answer", "decide_followup")

    g.add_conditional_edges(
        "decide_followup",
        lambda s: "ask_question" if s.get("should_follow_up") else "stage_transition",
        {
            "ask_question": "ask_question",
            "stage_transition": "stage_transition",
        }
    )

    g.add_conditional_edges(
        "stage_transition",
        check_done,
        {
            "ask_question": "ask_question",
            END: END,
        }
    )

    return g.compile()
