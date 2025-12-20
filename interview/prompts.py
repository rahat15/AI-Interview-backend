"""
interview/prompts.py
Stricter, stage-safe prompts to prevent technical contamination.
"""

# ---------------------------
# Strict Stage Instructions
# ---------------------------

STRICT_STAGE_INSTRUCTIONS = {

    "intro": """
Ask ONLY introductory and background questions.

Focus on:
- personal background
- career path
- interests related to the role
- high-level motivation

Rules:
- Questions must be non-technical.
- Do not assess skills or knowledge depth.
- Keep the tone conversational and welcoming.
- Questions should naturally connect to the candidate’s CV or career trajectory.

FORBIDDEN:
- technical concepts
- system design
- behavioral STAR questions
- HR or managerial evaluation
""",

    "hr": """
Ask ONLY HR and culture-fit questions.

Focus on:
- motivation for the role or company
- teamwork and collaboration
- communication style
- strengths and areas for growth
- workplace values and expectations

Rules:
- Keep questions people-focused, not skill-focused.
- Do not test technical ability or problem-solving.
- Avoid hypotheticals that resemble behavioral STAR questions.

FORBIDDEN:
- technical topics
- system design
- coding or tools
- behavioral STAR framing
""",

    "technical": """
Ask ONLY technical questions grounded in the Job Description and the candidate’s CV.

Focus on:
- skills, tools, or concepts explicitly mentioned in the JD or CV
- relevant engineering or ML fundamentals
- practical understanding and reasoning
- components, workflows, or design decisions within the candidate’s stated experience

Rules:
- Do NOT introduce technologies or domains not implied by the JD or CV.
- Prefer single-concept or single-component questions.
- Progress from conceptual understanding to deeper technical reasoning.
- Avoid repeating the same technology across multiple questions.
- Questions must be answerable without assuming senior-level ownership.

FORBIDDEN:
- HR, cultural, or personality questions
- behavioral STAR questions
- managerial or leadership evaluation
""",

    "behavioral": """
Ask ONLY behavioral questions using the STAR method.

Focus on:
- real past experiences
- challenges faced
- actions taken
- outcomes and learnings

Rules:
- Frame questions explicitly around past situations.
- Do not test technical knowledge.
- Do not ask hypothetical or future-oriented questions.
- Keep one experience per question.

FORBIDDEN:
- technical evaluation
- HR/culture-fit questions
- leadership or managerial assessment
""",

    "managerial": """
Ask ONLY leadership and ownership questions.

Focus on:
- decision-making
- prioritization
- ownership and accountability
- mentoring or guiding others
- handling conflict or ambiguity

Rules:
- Questions should assume responsibility or influence over others.
- Do not assess technical implementation details.
- Avoid STAR framing; focus on judgment and leadership mindset.

FORBIDDEN:
- technical questions
- HR/culture-fit questions
- behavioral STAR questions
""",

    "wrap-up": """
Ask ONLY closing questions.

Focus on:
- candidate questions
- expectations for the role
- next steps or timelines
- anything the candidate wants to clarify

Rules:
- Keep it light and open-ended.
- Do not introduce new evaluation topics.

FORBIDDEN:
- technical questions
- HR evaluation
- behavioral or managerial assessment
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
You are asking a follow-up question in a live interview.

Previous Question:
"{last_question}"

Candidate Answer:
"{last_answer}"

The candidate’s answer was incomplete or weak.

FOLLOW-UP RULES:
- Ask EXACTLY ONE natural follow-up question.
- Focus on the SINGLE weakest part of the candidate’s answer.
- Anchor the question to a SPECIFIC phrase, decision, or example the candidate mentioned.
- You MAY probe deeper into details already mentioned (why, how, tradeoffs, impact).
- Do NOT introduce a new domain or topic outside the answer.
- Do NOT ask generic clarification questions.

FORBIDDEN:
- "Can you elaborate?"
- "Can you clarify?"
- "Can you explain more?"
- Vague or filler follow-ups.

STYLE:
- Sound like a real human interviewer.
- Be precise and conversational.
- Max 30 words.
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
