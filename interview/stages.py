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
        "instruction": "Only background, ice-breakers, general conversation. No technical content."
    }

def hr_stage(state):
    return {
        "stage": "hr",
        "instruction": "Only HR/culture-fit topics. No technical, system design, or coding topics."
    }

def technical_stage(state):
    return {
        "stage": "technical",
        "instruction": "Technical questions ONLY: FastAPI, Redis, PostgreSQL, microservices, distributed systems."
    }

def behavioral_stage(state):
    return {
        "stage": "behavioral",
        "instruction": "STAR-format behavioral questions ONLY. No technical or HR questions."
    }

def managerial_stage(state):
    return {
        "stage": "managerial",
        "instruction": "Leadership, delegation, conflict, ownership questions ONLY. No technical content."
    }

def wrapup_stage(state):
    return {
        "stage": "wrap-up",
        "instruction": "Closing questions ONLY."
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
