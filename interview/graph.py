from langgraph.graph import StateGraph, END
from interview.stages import (
    intro_stage, hr_stage, technical_stage, behavioral_stage,
    managerial_stage, wrapup_stage
)

class InterviewState:
    stage: str
    asked_questions: list
    answers: list
    scores: dict
    config: dict

def build_dynamic_graph(config: dict):
    g = StateGraph(InterviewState)

    STAGES = {
        "intro_round": intro_stage,
        "hr_round": hr_stage,
        "technical_round": technical_stage,
        "behavioral_round": behavioral_stage,
        "managerial_round": managerial_stage,
        "final_round": wrapup_stage
    }

    level = config.get("level", "full_interview")

    if level == "intro_round":
        selected = ["intro_round", "hr_round", "final_round"]
    elif level == "technical_round":
        selected = ["intro_round", "technical_round", "behavioral_round", "final_round"]
    elif level == "behavioral_round":
        selected = ["behavioral_round", "final_round"]
    elif level == "hr_round":
        selected = ["hr_round", "final_round"]
    elif level == "managerial_round":
        selected = ["managerial_round", "final_round"]
    elif level == "full_interview":
        selected = [
            "intro_round",
            "technical_round",
            "behavioral_round",
            "hr_round",
            "managerial_round",
            "final_round"
        ]
    else:
        selected = ["final_round"]

    for stage in selected:
        g.add_node(stage, STAGES[stage])

    for i in range(len(selected) - 1):
        g.add_edge(selected[i], selected[i+1])

    g.add_edge(selected[-1], END)
    return g.compile()
