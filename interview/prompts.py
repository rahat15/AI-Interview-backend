"""
interview/prompts.py
Stricter, stage-safe prompts to prevent technical contamination.
"""

# ---------------------------
# Strict Stage Instructions
# ---------------------------

STRICT_STAGE_INSTRUCTIONS = {
    "intro": """
Ask ONLY introductory, background, small-talk, and career-path questions.
ABSOLUTELY DO NOT ask technical, HR, behavioral, or managerial questions.
""",

    "hr": """
Ask ONLY HR/culture-fit questions.
Allowed topics:
- motivation
- teamwork
- communication
- strengths & weaknesses
- workplace values
FORBIDDEN: any technical, system design, coding, algorithms, databases, or behavioral STAR questions.
""",

    "technical": """
Ask ONLY deep technical questions based on JD & CV.
Allowed topics:
- FastAPI
- Microservices
- Redis
- PostgreSQL
- Distributed systems
- System design
FORBIDDEN: HR, behavioral, managerial, cultural, or personality questions.
""",

    "behavioral": """
Ask ONLY STAR-method behavioral questions:
- Situation
- Task
- Action
- Result
FORBIDDEN: technical, HR/culture, personal, or leadership questions.
""",

    "managerial": """
Ask ONLY leadership, decision-making, delegation, mentoring, conflict resolution, delivery ownership questions.
FORBIDDEN: technical, STAR behavioral, HR cultural questions.
""",

    "wrap-up": """
Ask ONLY ending/closing questions.
Allowed:
- any questions for us?
- timeline?
- expectations?
FORBIDDEN: technical, HR, behavioral, managerial.
"""
}

# ---------------------------
# Main Question Prompt
# ---------------------------

BASE_QUESTION_PROMPT = """
You are an interviewer conducting the {stage} stage.

STRICT RULES:
{stage_instruction}

Context:
- Role: {role}
- Company: {company}
- Industry: {industry}

Candidate Profile:
- CV: {cv}
- Job Description: {jd}

Recent Q&A:
{history}

TASK:
- Ask EXACTLY ONE question.
- Max 20 words.
- No lists, no explanations.
- Must follow stage rules STRICTLY.
{followup_instructions}
"""

FOLLOWUP_INSTRUCTIONS = """
The candidate's previous answer was incomplete. Ask ONE clarification question ONLY about the last answer. 
Do NOT introduce any new topic.
"""

# ---------------------------
# Evaluation Prompt
# ---------------------------

BASE_EVALUATION_PROMPT = """
You are evaluating a candidate's answer. 
Return ONLY valid JSON. No explanations.

Context:
- Stage: {stage}
- Job Description: {jd}
- CV: {cv}

Question:
"{question}"

Answer:
"{answer}"

Instructions:
- "clarity" = communication quality (1-10)
- "confidence" = tone & conviction (1-10)
- "technical_depth" = technical relevance (1-10). If stage is NOT "technical", ALWAYS return 0.
- "summary" = 2-3 sentence concise evaluation.

Return JSON ONLY in this format:

{{
  "clarity": 0,
  "confidence": 0,
  "technical_depth": 0,
  "summary": ""
}}
"""


# ---------------------------
# Follow-up Decision
# ---------------------------

FOLLOWUP_DECISION_PROMPT = """
Stage: {stage}
Question: {question}
Answer: {answer}
Scores:
- clarity: {clarity}
- confidence: {confidence}
- technical_depth: {technical_depth}

Rules:
- HR/Intro/Behavioral/Managerial: max 1 follow-up.
- Technical: max 2 follow-ups.

Return JSON ONLY:
{
  "decision": "followup" or "stage_transition",
  "reason": "max 15 words"
}
"""
