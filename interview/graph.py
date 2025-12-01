from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal, Any
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision
from interview.stages import get_stage_order, get_max_questions  # Import your new helper

# ---------------------------
# State Definitions
# ---------------------------

class InterviewHistoryItem(TypedDict):
    question: str
    answer: str | None
    evaluation: dict | None
    stage: str
    is_followup: bool  # Added to track question count accurately

class InterviewState(TypedDict):
    stage: Literal["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    jd: str
    cv: str
    session_config: dict  # RENAMED from 'config' to fix ChannelWrite error
    history: List[InterviewHistoryItem]
    should_follow_up: bool
    completed: bool       # Added to track interview completion

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
        "is_followup": followup  # Mark as followup
    })

    # Reset follow-up flag
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState, **kwargs) -> InterviewState:
    """Evaluate candidate's answer."""
    # Safety check: if no history, skip
    if not state["history"]:
        return state

    last = state["history"][-1]
    
    # If no answer provided yet, skip (shouldn't happen in turn-based flow)
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
    """
    Transition to next stage based on stages.py configuration.
    Only counts 'main' questions (not follow-ups) towards the limit.
    """
    # If a follow-up is explicitly requested, do not change stage
    if state.get("should_follow_up"):
        return state

    # 1. Get configuration
    # Use .get() safely for session_config
    config = state.get("session_config", {}) 
    round_type = config.get("round_type", "full")
    current_stage = state["stage"]

    # 2. Count MAIN questions in the current stage
    # We filter out items where is_followup is True
    history = state.get("history", [])
    current_stage_count = sum(
        1 for h in history 
        if h.get("stage") == current_stage and not h.get("is_followup", False)
    )

    # 3. Check limit from stages.py
    limit = get_max_questions(round_type, current_stage)

    # 4. Transition if limit reached
    if current_stage_count >= limit:
        order = get_stage_order(round_type)
        try:
            curr_idx = order.index(current_stage)
            if curr_idx + 1 < len(order):
                # Move to next stage
                state["stage"] = order[curr_idx + 1]
            else:
                # No more stages -> Mark completed
                state["completed"] = True
        except ValueError:
            # Fallback if current stage is unknown
            state["completed"] = True

    return state


# ---------------------------
# Routing Logic (Fixes Recursion Loop)
# ---------------------------

def route_start(state: InterviewState):
    """
    Determine entry point.
    - If new session (no history) -> Ask Question.
    - If resuming (has history) -> Evaluate Answer.
    """
    if not state.get("history"):
        return "ask_question"
    return "evaluate_answer"


def check_done(state: InterviewState):
    """
    Determine if we should continue interviewing or end.
    """
    if state.get("completed"):
        return END
    return "ask_question"


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

    # 1. Dynamic Entry Point
    # This prevents the loop by intelligently jumping to evaluation when an answer exists
    g.set_conditional_entry_point(
        route_start,
        {
            "ask_question": "ask_question",
            "evaluate_answer": "evaluate_answer"
        }
    )

    # 2. Ask -> END
    # This pauses execution to wait for user input (API response)
    g.add_edge("ask_question", END)

    # 3. Evaluate -> Decide
    g.add_edge("evaluate_answer", "decide_followup")

    # 4. Decide -> (Followup OR Transition)
    g.add_conditional_edges(
        "decide_followup",
        lambda s: "ask_question" if s.get("should_follow_up") else "stage_transition",
        {
            "ask_question": "ask_question",
            "stage_transition": "stage_transition",
        }
    )

    # 5. Transition -> (Ask OR End)
    # Checks if the interview is marked completed
    g.add_conditional_edges(
        "stage_transition",
        check_done,
        {
            "ask_question": "ask_question",
            END: END
        }
    )

    # Compile & return
    compiled = g.compile()
    return compiled