def should_followup(eval_result: dict) -> bool:
    """
    Decide if a follow-up question is needed.
    Example heuristic: if any score < 5, ask a follow-up.
    """
    scores = [eval_result.get(k, 10) for k in ["technical_depth", "relevance", "communication", "behavioral"]]
    return any(s < 5 for s in scores)
