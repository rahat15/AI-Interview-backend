def intro_stage(state):
    return {"stage": "intro_round", "instruction": "Start with CV highlights and small talk."}

def hr_stage(state):
    return {"stage": "hr_round", "instruction": "Ask about motivations, culture fit, strengths, weaknesses."}

def technical_stage(state):
    return {"stage": "technical_round", "instruction": "Ask role-specific technical questions from JD and CV."}

def behavioral_stage(state):
    return {"stage": "behavioral_round", "instruction": "Ask STAR-based behavioral questions."}

def managerial_stage(state):
    return {"stage": "managerial_round", "instruction": "Ask leadership and decision-making scenarios."}

def wrapup_stage(state):
    return {"stage": "final_round", "instruction": "Ask final closing questions and give wrap-up."}
