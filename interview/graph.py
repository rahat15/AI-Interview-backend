from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from interview.stages import get_stage_order, get_max_questions
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer, summarize_scores
from interview.followup import followup_decision

# ---------------------------
# Define State
# ---------------------------

class InterviewState(TypedDict):
    config: dict
    jd: str
    cv: str
    stage: str
    stage_index: int
    question_count: int
    history: List[Dict[str, Any]]  # {stage, question, answer, evaluation}

# ---------------------------
# Node Functions
# ---------------------------

async def ask_question(state: InterviewState) -> InterviewState:
    q = await generate_question(state, state["stage"])
    state["question_count"] += 1
    state["history"].append({"stage": state["stage"], "question": q})
    return state

async def evaluate_answer_node(state: InterviewState) -> InterviewState:
    last = state["history"][-1]
    evaluation = await evaluate_answer(
        stage=state["stage"],
        question=last["question"],
        user_answer=last.get("answer", ""),
        jd=state["jd"],
        cv=state["cv"]
    )
    last["evaluation"] = evaluation
    return state

async def followup_node(state: InterviewState) -> str:
    decision = await followup_decision(state)
    if decision["decision"] == "followup":
        return "ask_question"
    return "stage_transition"

async def stage_transition(state: InterviewState) -> str:
    # If stage has more Qs left → keep asking
    max_qs = get_max_questions(state["config"]["round_type"], state["stage"])
    if state["question_count"] < max_qs:
        return "ask_question"

    # Otherwise move to next stage
    state["stage_index"] += 1
    if state["stage_index"] >= len(state["config"]["stages"]):
        return "end"
    state["stage"] = state["config"]["stages"][state["stage_index"]]
    state["question_count"] = 0
    return "ask_question"

async def end_node(state: InterviewState) -> dict:
    summary = summarize_scores([h.get("evaluation", {}) for h in state["history"]])
    return {"end": True, "summary": summary, "history": state["history"]}

# ---------------------------
# Build Graph
# ---------------------------

def build_graph(config: dict, jd: str, cv: str):
    g = StateGraph(InterviewState)

    stages = get_stage_order(config.get("round_type", "default"))
    init_state: InterviewState = {
        "config": {**config, "stages": stages},
        "jd": jd,
        "cv": cv,
        "stage": stages[0],
        "stage_index": 0,
        "question_count": 0,
        "history": []
    }

    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    g.add_node("followup", followup_node)
    g.add_node("stage_transition", stage_transition)
    g.add_node("end", end_node)

    g.set_entry_point("ask_question")
    g.add_edge("ask_question", "evaluate_answer")
    g.add_edge("evaluate_answer", "followup")
    g.add_conditional_edges("followup", {"ask_question": "ask_question", "stage_transition": "stage_transition"})
    g.add_conditional_edges("stage_transition", {"ask_question": "ask_question", "end": "end"})

    return g.compile(initial_state=init_state)
