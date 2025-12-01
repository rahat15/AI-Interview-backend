from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal, Any
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision


# ---------------------------
# State Definitions
# ---------------------------

class InterviewHistoryItem(TypedDict):
    question: str
    answer: str | None
    evaluation: dict | None
    stage: str


class InterviewState(TypedDict):
    stage: Literal["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    jd: str
    cv: str
    config: dict
    history: List[InterviewHistoryItem]
    should_follow_up: bool


# ---------------------------
# Graph Nodes
# ---------------------------

async def ask_question(state: InterviewState, **kwargs) -> InterviewState:
    """Generate and append a question."""
    stage = state["stage"]
    followup = state.get("should_follow_up", False)

    q = await generate_question(state, stage, followup)

    state["history"].append({
        "question": q,
        "answer": None,
        "evaluation": None,
        "stage": stage,
    })

    # Reset follow-up flag
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState, **kwargs) -> InterviewState:
    """Evaluate candidate's answer."""
    if not state["history"]:
        return state

    last = state["history"][-1]
    if not last.get("answer"):
        return state

    evaluation = await evaluate_answer(
        user_answer=last["answer"],
        jd=state["jd"],
        cv=state["cv"]
    )

    last["evaluation"] = evaluation
    return state


async def decide_followup_node(state: InterviewState, **kwargs) -> InterviewState:
    """Decide whether to follow up or move to the next stage."""
    decision = await followup_decision(state)
    state["should_follow_up"] = (decision.get("decision") == "followup")
    return state


def stage_transition_node(state: InterviewState, **kwargs) -> InterviewState:
    """Transition to next stage if not following up."""
    if state.get("should_follow_up"):
        return state

    stages = ["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    current = state["stage"]

    try:
        idx = stages.index(current)
        if idx + 1 < len(stages):
            state["stage"] = stages[idx + 1]
    except ValueError:
        state["stage"] = "wrap-up"

    return state


# ---------------------------
# Graph Builder
# ---------------------------

def build_graph(config: dict) -> Any:
    """Compile the LangGraph finite state machine for this session."""

    g = StateGraph(InterviewState)

    # Register nodes
    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    g.add_node("decide_followup", decide_followup_node)
    g.add_node("stage_transition", stage_transition_node)

    # Entry point
    g.set_entry_point("ask_question")

    # Workflow edges
    g.add_edge("ask_question", "evaluate_answer")
    g.add_edge("evaluate_answer", "decide_followup")

    # If follow-up → ask_question again, else stage transition
    g.add_conditional_edges(
        "decide_followup",
        lambda s: "ask_question" if s.get("should_follow_up") else "stage_transition",
        {
            "ask_question": "ask_question",
            "stage_transition": "stage_transition",
        }
    )

    # Handle stage progression until wrap-up
    def next_step(state: InterviewState):
        return END if state["stage"] == "wrap-up" else "ask_question"

    g.add_conditional_edges(
        "stage_transition",
        next_step,
        {
            "ask_question": "ask_question",
            END: END
        }
    )

    # Compile & return
    compiled = g.compile()
    return compiled
