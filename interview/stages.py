"""
interview/stages.py
Core stage definitions and stage order resolution.
"""

# ---------------------------
# Stage Definitions
# ---------------------------

def intro_stage(state):
    return {
        "stage": "intro",
        "instruction": "Start with CV highlights, small talk, and ice-breaker questions."
    }

def hr_stage(state):
    return {
        "stage": "hr",
        "instruction": "Ask about motivations, culture fit, strengths, and weaknesses."
    }

def technical_stage(state):
    return {
        "stage": "technical",
        "instruction": "Ask role-specific technical questions from JD and CV."
    }

def behavioral_stage(state):
    return {
        "stage": "behavioral",
        "instruction": "Ask STAR-based behavioral questions (Situation, Task, Action, Result)."
    }

def managerial_stage(state):
    return {
        "stage": "managerial",
        "instruction": "Ask leadership, decision-making, and conflict resolution scenarios."
    }

def wrapup_stage(state):
    return {
        "stage": "wrap-up",
        "instruction": "Ask final closing questions, candidate queries, and wrap-up."
    }

# ---------------------------
# Question Count Configuration
# ---------------------------

QUESTION_CONFIG = {
    "full": {
        "intro": 1,
        "hr": 2,
        "technical": 3,
        "behavioral": 2,
        "managerial": 1,
        "wrap-up": 1
    },
    "hr": {
        "intro": 1,
        "hr": 4,
        "wrap-up": 1
    },
    "technical": {
        "intro": 1,
        "technical": 5,
        "wrap-up": 1
    },
    "behavioral": {
        "intro": 1,
        "behavioral": 3,
        "wrap-up": 1
    },
    "managerial": {
        "intro": 1,
        "managerial": 3,
        "wrap-up": 1
    },
    "default": {
        "intro": 1,
        "technical": 3,
        "wrap-up": 1
    }
}

# ---------------------------
# Helpers
# ---------------------------

def get_stage_order(round_type: str) -> list:
    """Return the sequence of stages based on round type."""
    round_type = (round_type or "default").lower()
    if round_type in QUESTION_CONFIG:
        return list(QUESTION_CONFIG[round_type].keys())
    return list(QUESTION_CONFIG["default"].keys())

def get_max_questions(round_type: str, stage: str) -> int:
    """Return the number of questions allowed for a stage."""
    round_type = (round_type or "default").lower()
    config = QUESTION_CONFIG.get(round_type, QUESTION_CONFIG["default"])
    return config.get(stage, 1)
