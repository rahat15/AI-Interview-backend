from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal

# Assume these are your imported async functions
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision

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
    history: List[InterviewHistoryItem]
    should_follow_up: bool

# ---- Flow Nodes (with added debugging) ----

async def ask_question(state: InterviewState) -> InterviewState:
    # --- DEBUGGING STEP 1 ---
    # Check if the imported function is valid before calling it.
    print(f"DEBUG >> Is generate_question a function? {callable(generate_question)}")
    if not callable(generate_question):
        raise TypeError("Imported 'generate_question' is not a callable function. Check for circular imports.")

    stage = state.get("stage", "intro")
    followup = state.get("should_follow_up", False)
    q = await generate_question(state, stage, followup)
    
    if "history" not in state:
        state["history"] = []
    state["history"].append({"question": q, "answer": None, "evaluation": None, "stage": stage})
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState) -> InterviewState:
    if not state.get("history") or not state["history"][-1].get("answer"):
        return state

    last_entry = state["history"][-1]

    # --- DEBUGGING STEP 2 ---
    print(f"DEBUG >> Is evaluate_answer a function? {callable(evaluate_answer)}")
    if not callable(evaluate_answer):
        raise TypeError("Imported 'evaluate_answer' is not a callable function. Check for circular imports.")
        
    eval_result = await evaluate_answer(
        user_answer=last_entry["answer"],
        jd=state.get("jd", ""),
        cv=state.get("cv", ""),
    )
    last_entry["evaluation"] = eval_result
    state["history"][-1] = last_entry
    return state


def decide_followup_node(state: InterviewState) -> InterviewState:
    state["should_follow_up"] = False
    if not state.get("history"):
        return state
        
    last_entry = state["history"][-1]
    eval_result = last_entry.get("evaluation")

    if eval_result:
        # --- DEBUGGING STEP 3 ---
        print(f"DEBUG >> Is followup_decision a function? {callable(followup_decision)}")
        if not callable(followup_decision):
            raise TypeError("Imported 'followup_decision' is not a callable function. Check for circular imports.")

        print(f"DEBUG >> Calling followup_decision with: {eval_result}")
        decision = followup_decision(eval_result)
        print(f"DEBUG >> followup_decision returned: {decision}")
        state["should_follow_up"] = bool(decision)
        
    return state


def stage_transition_node(state: InterviewState) -> InterviewState:
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

    return g.compile()