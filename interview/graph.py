from langgraph.graph import StateGraph, END
from interview.question import generate_question
from interview.evaluate.judge import evaluate_answer
from interview.followup import followup_decision


class InterviewState(dict):
    pass


# ---- Flow Nodes ----

async def ask_question(state: InterviewState) -> InterviewState:
    stage = state.get("stage", "intro")
    followup = state.get("should_follow_up", False)

    q = await generate_question(state, stage, followup)
    state.setdefault("history", []).append(
        {"question": q, "answer": None, "evaluation": None, "stage": stage}
    )
    state["should_follow_up"] = False
    return state


async def evaluate_answer_node(state: InterviewState) -> InterviewState:
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
    last = state["history"][-1] if state.get("history") else {}
    eval_result = last.get("evaluation", {})
    state["should_follow_up"] = followup_decision(eval_result)
    return state


def stage_transition(state: InterviewState) -> InterviewState:
    if state.get("should_follow_up"):
        return state

    stages = ["intro", "technical", "behavioral", "hr", "managerial", "wrap-up"]
    current = state.get("stage", "intro")

    try:
        idx = stages.index(current)
        state["stage"] = stages[idx + 1] if idx + 1 < len(stages) else "wrap-up"
    except ValueError:
        state["stage"] = "wrap-up"

    return state


# ---- Graph Build ----

def build_graph(config: dict):
    g = StateGraph(InterviewState)

    g.add_node("ask_question", ask_question)
    g.add_node("evaluate_answer", evaluate_answer_node)
    g.add_node("followup_decision", followup_node)
    g.add_node("stage_transition", stage_transition)

    g.set_entry_point("ask_question")

    g.add_edge("ask_question", "evaluate_answer")
    g.add_edge("evaluate_answer", "followup_decision")

    # Branch after followup_decision
    g.add_conditional_edges(
        "followup_decision",
        lambda state: "ask_question" if state.get("should_follow_up") else "stage_transition",
        {
            "ask_question": "ask_question",
            "stage_transition": "stage_transition",
        },
    )

    # ✅ Branch after stage_transition
    def decide_next(state: InterviewState) -> str:
        print("DEBUG >> stage_transition sees stage =", state.get("stage"))
        return "end" if state.get("stage") == "wrap-up" else "ask_question"


    g.add_conditional_edges(
        "stage_transition",
        decide_next,
        {
            "end": END,
            "ask_question": "ask_question",
        },
    )

    return g.compile()
