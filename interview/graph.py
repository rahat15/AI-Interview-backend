from langgraph.graph import StateGraph, END
from interview.stages import (
    intro_stage, hr_stage, technical_stage,
    behavioral_stage, managerial_stage, wrapup_stage,
)
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision


# ---- Shared State ----
class InterviewState(dict):
    """
    State is a dict-like object tracking interview progress.
    Keys:
        - stage: current stage (intro/hr/etc.)
        - history: list of {question, answer, evaluation}
        - should_follow_up: bool
        - config: role, company, industry
        - jd, cv: text data
    """
    pass


# ---- Graph Node Functions ----

async def ask_question(state: InterviewState) -> InterviewState:
    """Generate a new question based on stage & history."""
    stage = state.get("stage", "intro")
    followup = state.get("should_follow_up", False)

    q = await generate_question(
        state=state,
        stage=stage,
        followup=followup,
    )

    state.setdefault("history", []).append(
        {"question": q, "answer": None, "evaluation": None, "stage": stage}
    )
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState) -> InterviewState:
    """Evaluate the last answer."""
    if not state.get("history"):
        return state

    last = state["history"][-1]
    if not last.get("answer"):
        return state

    eval_result = await evaluate_answer(
        user_answer=last["answer"],
        jd=state.get("jd", ""),
        cv=state.get("cv", ""),
    )
    last["evaluation"] = eval_result
    state["history"][-1] = last
    return state


def followup_node(state: InterviewState) -> InterviewState:
    """Decide if a follow-up is needed."""
    last = state["history"][-1] if state.get("history") else {}
    eval_result = last.get("evaluation", {})

    state["should_follow_up"] = followup_decision(eval_result)
    return state


def stage_transition(state: InterviewState) -> InterviewState:
    """Move to the next stage if no follow-up is required."""
    if state.get("should_follow_up"):
        return state  # stay in same stage

    stages = ["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    current = state.get("stage", "intro")

    try:
        idx = stages.index(current)
        state["stage"] = stages[idx + 1] if idx + 1 < len(stages) else "wrap-up"
    except ValueError:
        state["stage"] = "wrap-up"

    return state


# ---- Build Graph ----

def build_graph(config: dict):
    g = StateGraph(InterviewState)

    # Register stage nodes (setup/instruction)
    g.add_node("intro", intro_stage)
    g.add_node("hr", hr_stage)
    g.add_node("technical", technical_stage)
    g.add_node("behavioral", behavioral_stage)
    g.add_node("managerial", managerial_stage)
    g.add_node("wrap-up", wrapup_stage)

    # Register flow nodes
    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    g.add_node("followup_decision", followup_node)
    g.add_node("stage_transition", stage_transition)

    # Wire edges
    g.set_entry_point("ask_question")

    g.add_edge("ask_question", "evaluate_answer")
    g.add_edge("evaluate_answer", "followup_decision")
    g.add_edge("followup_decision", "ask_question")       # if follow-up needed
    g.add_edge("followup_decision", "stage_transition")   # else advance stage
    g.add_edge("stage_transition", "ask_question")

    g.add_edge("wrap-up", END)  # end interview

    return g.compile()
