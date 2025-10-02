from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal

# Assume these are your imported async functions
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision

# --- It's best practice to define your state shape with TypedDict ---
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

# ---- Flow Nodes (with added robustness) ----

async def ask_question(state: InterviewState) -> InterviewState:
    stage = state.get("stage", "intro")
    followup = state.get("should_follow_up", False)

    q = await generate_question(state, stage, followup)
    
    # Initialize the history list if it doesn't exist
    if "history" not in state:
        state["history"] = []
        
    state["history"].append(
        {"question": q, "answer": None, "evaluation": None, "stage": stage}
    )
    # Reset the follow-up flag after asking the question
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState) -> InterviewState:
    if not state.get("history"):
        return state

    last_entry = state["history"][-1]
    # This check is crucial: only evaluate if there is an answer
    if not last_entry.get("answer"):
        print("DEBUG >> Skipping evaluation because no answer was provided.")
        return state

    eval_result = await evaluate_answer(
        user_answer=last_entry["answer"],
        jd=state.get("jd", ""),
        cv=state.get("cv", ""),
    )
    last_entry["evaluation"] = eval_result
    state["history"][-1] = last_entry
    return state


def decide_followup_node(state: InterviewState) -> InterviewState:
    # Default to False if something goes wrong
    state["should_follow_up"] = False
    
    if not state.get("history"):
        return state
        
    last_entry = state["history"][-1]
    eval_result = last_entry.get("evaluation")

    # Only decide if there was an evaluation to begin with
    if eval_result:
        # Ensure followup_decision returns a boolean, not None
        decision = followup_decision(eval_result)
        state["should_follow_up"] = bool(decision) # Coerce None to False
        
    return state


def stage_transition_node(state: InterviewState) -> InterviewState:
    # This node should only run if we are NOT following up
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
        # If current stage isn't in the list, default to wrap-up
        state["stage"] = "wrap-up"

    return state


# ---- Graph Build ----

def build_graph():
    # Using the TypedDict for better type hinting and clarity
    g = StateGraph(InterviewState)

    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    # Renamed for clarity to avoid conflict with imported function
    g.add_node("decide_followup", decide_followup_node)
    g.add_node("stage_transition", stage_transition_node)

    g.set_entry_point("ask_question")

    g.add_edge("ask_question", "evaluate_answer")
    g.add_edge("evaluate_answer", "decide_followup")

    # Branch after deciding on a followup
    g.add_conditional_edges(
        "decide_followup",
        # This lambda function decides which path to take
        lambda state: "ask_question" if state.get("should_follow_up") else "stage_transition",
    )

    # Branch after stage transition
    def decide_next_step(state: InterviewState) -> str:
        print("DEBUG >> In decide_next_step, current stage is:", state.get("stage"))
        if state.get("stage") == "wrap-up":
            return END
        else:
            return "ask_question"

    g.add_conditional_edges(
        "stage_transition",
        decide_next_step,
        # Note: You can also use the simplified syntax if the map is 1:1 with return values
        # In the previous conditional edge, the map was omitted because the lambda's
        # return values ("ask_question", "stage_transition") are the names of the nodes.
        # Here, we need a map because we return END, which is not a node name.
        {
            "ask_question": "ask_question",
            END: END
        }
    )

    return g.compile()