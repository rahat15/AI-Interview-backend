def apply_rules(answer: str, jd: str) -> dict:
    """
    Apply heuristic rules on answers.
    Example: penalize if JD mentions 'Python' but candidate never does.
    """
    result = {}
    if "python" in jd.lower() and "python" not in answer.lower():
        result["penalty"] = "Candidate did not mention Python though it is in JD."
    return result
