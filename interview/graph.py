from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal
import asyncio

# Assume these are your imported async functions
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision

# ======================================================================
# AGGRESSIVE DEBUGGING: CHECK IMPORTS IMMEDIATELY WHEN THE FILE IS LOADED
# ======================================================================
print("--- MODULE LEVEL IMPORT CHECK ---")
print(f"generate_question is callable: {callable(generate_question)}")
print(f"evaluate_answer is callable: {callable(evaluate_answer)}")
print(f"followup_decision is callable: {callable(followup_decision)}")
print("---------------------------------")

# This will crash the app on startup if an import is broken.
if not all([callable(generate_question), callable(evaluate_answer), callable(followup_decision)]):
    # Find which one is the problem
    if not callable(generate_question):
        raise ImportError("'generate_question' is not callable. Check your imports, especially for circular dependencies.")
    if not callable(evaluate_answer):
        raise ImportError("'evaluate_answer' is not callable. Check your imports, especially for circular dependencies.")
    if not callable(followup_decision):
        raise ImportError("'followup_decision' is not callable. Check your imports, especially for circular dependencies.")
# ======================================================================


# --- State Definition ---
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

# ---- Flow Nodes ----

async def ask_question(state: InterviewState) -> InterviewState:
    """Generate and append a question to history."""
    stage = state.get("stage", "intro")
    followup = state.get("should_follow_up", False)
    q = await generate_question(state, stage, followup)
    if "history" not in state:
        state["history"] = []
    state["history"].append({"question": q, "answer": None, "evaluation": None, "stage": stage})
    state["should_follow_up"] = False
    return state

async def evaluate_answer_node(state: InterviewState) -> InterviewState:
    """Evaluate the user's answer."""
    if not state.get("history") or not state["history"][-1].get("answer"):
        return state
    last_entry = state["history"][-1]
    eval_result = await evaluate_answer(
        user_answer=last_entry["answer"],
        jd=state.get("jd", ""),
        cv=state.get("cv", ""),
    )
    last_entry["evaluation"] = eval_result
    state["history"][-1] = last_entry
    return state

async def decide_followup_node(state: InterviewState) -> InterviewState:
    """
    FIXED: Now async to await followup_decision, and passes full state instead of just eval_result.
    """
    state["should_follow_up"] = False
    if not state.get("history"):
        return state
    
    # Call async followup_decision with full state
    decision_result = await followup_decision(state)
    
    # Extract decision from result (result is {"decision": "followup" | "stage_transition", "reason": str})
    if decision_result.get("decision") == "followup":
        state["should_follow_up"] = True
    
    return state

def stage_transition_node(state: InterviewState) -> InterviewState:
    """Advance to next stage unless follow-up is requested."""
    if state.get("should_follow_up"):
        return state
    stages = ["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    current_stage = state.get("stage", "intro")
    try:
        current_idx = stages.index(current_stage)
        next_idx = current_idx + 1
        if next_idx < len(stages):
            state["stage"] = stages[next_idx]
        else:
            state["stage"] = "wrap-up"
    except ValueError:
        state["stage"] = "wrap-up"
    return state

# ---- Graph Build ----
def build_graph(config: dict):
    """Build and compile the interview state machine."""
    g = StateGraph(InterviewState)
    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    g.add_node("decide_followup", decide_followup_node)
    g.add_node("stage_transition", stage_transition_node)
    g.set_entry_point("ask_question")
    g.add_edge("ask_question", "evaluate_answer")
    g.add_edge("evaluate_answer", "decide_followup")
    g.add_conditional_edges(
        "decide_followup",
        lambda state: "ask_question" if state.get("should_follow_up") else "stage_transition",
        {
            "ask_question": "ask_question",
            "stage_transition": "stage_transition",
        }
    )

    def decide_next_step(state: InterviewState) -> str:
        if state.get("stage") == "wrap-up":
            return END
        else:
            return "ask_question"
    
    g.add_conditional_edges(
        "stage_transition",
        decide_next_step,
        { "ask_question": "ask_question", END: END }
    )
    
    compiled = g.compile()
    print(f"✅ Graph compiled successfully: {compiled}")
    return compiled