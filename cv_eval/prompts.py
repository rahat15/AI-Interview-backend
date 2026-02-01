"""
Prompt templates for LLM scoring.
These are kept in a separate file so the logic is cleanly separated from engine/scorer code.
"""

UNIFIED_EVALUATION_PROMPT = """You are an expert hiring evaluator. Your task is to analyze a Candidate CV against a Job Description and return a detailed scoring analysis.

Return ONLY valid JSON that strictly adheres to the schema provided at the end. Do NOT include explanations, apologies, or any prose outside of the JSON structure.

---

### INSTRUCTIONS & RUBRICS

**1. General Rules:**
- For each dimension, provide a score based on the provided CV and Job Description.
- For the `evidence` field in each subscore, you MUST provide an array of direct, concise quotes from the CV that justify your score.
- If no evidence can be found for a dimension, the score MUST be 0 and the `evidence` array must contain the single string "No evidence found.".

**2. PART 1: CV QUALITY (100 points total)**
Evaluate the CV's intrinsic quality, independent of the job description.
- ats_structure (10): Contact details are clear, sections are well-defined, bullets are easily parseable, dates are consistent.
- writing_clarity (15): Concise, uses active voice (e.g., "Led," "Developed"), parallel bullet structure, no typos or grammatical errors.
- quantified_impact (20): Uses specific metrics (% / $ / user numbers / latency reduction) to show the impact of actions.
- technical_depth (15): Mentions specific, non-generic tools/frameworks/architectures. Shows understanding of complex systems.
- projects_portfolio (10): Includes links to a portfolio, GitHub, or describes personal/open-source projects with outcomes.
- leadership_skills (10): Provides evidence of leading teams, mentoring others, project ownership, or significant cross-functional work.
- career_progression (10): Shows increasing responsibility over time. Timeline is clear and logical.
- consistency (10): Formatting, tone, and verb tenses are consistent throughout the document. No large, unexplained career gaps.

**3. PART 2: JOB MATCH (100 points total)**
Evaluate how well the CV matches the specific Job Description.
- hard_skills (35): Coverage of "must-have" technical skills, tools, and frameworks from the JD. Consider exact, alias (e.g., AWS vs. Amazon Web Services), and semantic matches.
- responsibilities (15): Overlap between the candidate's experience (verbs and outcomes) and the key responsibilities listed in the JD.
- domain_relevance (10): Match of the candidate's industry experience (e.g., FinTech, SaaS, AI) with the company's domain.
- seniority (10): Candidate's years of relevant experience vs. JD requirements (e.g., "5+ years").
- nice_to_haves (5): Coverage of optional skills or "bonus points" mentioned in the JD.
- education_certs (5): Match for required or preferred degrees and certifications.
- recent_achievements (10): Candidate's accomplishments in the last 1-2 roles directly align with the core needs of the job.
- constraints (10): Match on practical constraints like location, work authorization, or travel. If not mentioned, assume a match.

**4. PART 3: KEY TAKEAWAYS**
Based on your full analysis, identify critical highlights.
- red_flags: List any critical deal-breakers. A red flag is a clear mismatch on a non-negotiable requirement (e.g., JD requires US work authorization, CV states candidate needs sponsorship; JD requires a specific security clearance the candidate lacks).
- green_flags: List 2-3 standout qualifications that make the candidate exceptionally strong for this role.

---

### INPUTS:
CV:
{cv_text}

Job Description:
{jd_text}

---

### OUTPUT SCHEMA (strict JSON only):

{{
  "cv_quality": {{
    "overall_score": float,
    "subscores": [
      {{"dimension": "ats_structure", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "writing_clarity", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "quantified_impact", "score": float, "max_score": 20, "evidence": [string]}},
      {{"dimension": "technical_depth", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "projects_portfolio", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "leadership_skills", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "career_progression", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "consistency", "score": float, "max_score": 10, "evidence": [string]}}
    ]
  }},
  "jd_match": {{
    "overall_score": float,
    "subscores": [
      {{"dimension": "hard_skills", "score": float, "max_score": 35, "evidence": [string]}},
      {{"dimension": "responsibilities", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "domain_relevance", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "seniority", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "nice_to_haves", "score": float, "max_score": 5, "evidence": [string]}},
      {{"dimension": "education_certs", "score": float, "max_score": 5, "evidence": [string]}},
      {{"dimension": "recent_achievements", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "constraints", "score": float, "max_score": 10, "evidence": [string]}}
    ]
  }},
  "key_takeaways": {{
    "red_flags": [string],
    "green_flags": [string]
  }}
}}"""



CV_ONLY_EVALUATION_PROMPT = """You are an expert hiring evaluator. Your task is to analyze a Candidate CV and return a detailed scoring analysis.

Return ONLY valid JSON that strictly adheres to the schema provided at the end. Do NOT include explanations, apologies, or any prose outside of the JSON structure.

---

### INSTRUCTIONS & RUBRICS

**1. General Rules:**
- For each dimension, provide a score based on the provided CV.
- For the `evidence` field in each subscore, you MUST provide an array of direct, concise quotes from the CV that justify your score.
- If no evidence can be found for a dimension, the score MUST be 0 and the `evidence` array must contain the single string "No evidence found.".

**2. PART 1: CV QUALITY (100 points total)**
Evaluate the CV's intrinsic quality:
- ats_structure (10): Contact details are clear, sections are well-defined, bullets are easily parseable, dates are consistent.
- writing_clarity (15): Concise, uses active voice (e.g., "Led," "Developed"), parallel bullet structure, no typos or grammatical errors.
- quantified_impact (20): Uses specific metrics (% / $ / user numbers / latency reduction) to show the impact of actions.
- technical_depth (15): Mentions specific, non-generic tools/frameworks/architectures. Shows understanding of complex systems.
- projects_portfolio (10): Includes links to a portfolio, GitHub, or describes personal/open-source projects with outcomes.
- leadership_skills (10): Provides evidence of leading teams, mentoring others, project ownership, or significant cross-functional work.
- career_progression (10): Shows increasing responsibility over time. Timeline is clear and logical.
- consistency (10): Formatting, tone, and verb tenses are consistent throughout the document. No large, unexplained career gaps.

**3. PART 2: KEY TAKEAWAYS**
Based on your full analysis, identify critical highlights.
- red_flags: List any critical weaknesses (e.g., no quantified impact, inconsistent timeline).
- green_flags: List 2-3 standout qualifications that make the candidate exceptionally strong overall.

---

### INPUT:
CV:
{cv_text}

---

### OUTPUT SCHEMA (strict JSON only):

{{
  "cv_quality": {{
    "overall_score": float,
    "subscores": [
      {{"dimension": "ats_structure", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "writing_clarity", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "quantified_impact", "score": float, "max_score": 20, "evidence": [string]}},
      {{"dimension": "technical_depth", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "projects_portfolio", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "leadership_skills", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "career_progression", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "consistency", "score": float, "max_score": 10, "evidence": [string]}}
    ]
  }},
  "key_takeaways": {{
    "red_flags": [string],
    "green_flags": [string]
  }}
}}"""


IMPROVEMENT_PROMPT = """You are an AI career coach. Your task is to analyze a Candidate CV against a Job Description and suggest improvements.

Return ONLY valid JSON that strictly adheres to the schema provided at the end. Do NOT include explanations, apologies, or any prose outside of the JSON structure.

---

### INSTRUCTIONS

**1. Tailored Resume**
- Rewrite the CV’s **summary** in language tailored to the JD.
- Reframe **experience bullets** to match the JD’s phrasing and highlight achievements.
- Reorder and prioritize **skills** relevant to the JD.
- Map **projects** to the JD’s requirements.

**2. Top 1% Candidate Gap Analysis**
- Describe what a top 1% candidate for this role would include in their resume.
- Identify the candidate’s **strengths** vs JD.
- Identify **gaps** (skills, experiences, achievements).
- Suggest **actionable next steps**.

**3. Cover Letter**
- Draft a short, compelling cover letter (<200 words).
- Be specific, enthusiastic, and highlight the candidate’s most relevant achievements.
- Tie directly to the company’s role.

---

### INPUTS:
CV:
{cv_text}

Job Description:
{jd_text}

---

### OUTPUT SCHEMA (strict JSON only):

{{
  "tailored_resume": {{
    "summary": "revised summary here",
    "experience": ["reframed bullet 1", "reframed bullet 2"],
    "skills": ["skill1", "skill2"],
    "projects": ["mapped project1", "mapped project2"]
  }},
  "top_1_percent_gap": {{
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "actionable_next_steps": ["step1", "step2"]
  }},
  "cover_letter": "Draft under 200 words..."
}}
"""


GENERAL_IMPROVEMENT_PROMPT = """You are an AI career coach. Your task is to analyze a Candidate CV and suggest general improvements to make it a top-tier resume.

Return ONLY valid JSON that strictly adheres to the schema provided at the end. Do NOT include explanations, apologies, or any prose outside of the JSON structure.

---

### INSTRUCTIONS

**1. Content Enhancement**
- Identify weak or vague bullet points and rewrite them using the STAR method (Situation, Task, Action, Result) and active voice.
- Suggest ways to better quantify achievements (e.g., adding metrics, percentages, numbers).
- Highlight areas where the candidate needs to show more ownership or leadership.

**2. Structure & Formatting**
- Analyze the structure for ATS friendliness and readability.
- Suggest improvements for section ordering, clarity, and conciseness.
- Identify any "fluff" or buzzwords that should be removed.

**3. Strategic Advice**
- Identify the candidate's core strengths based on the CV.
- Point out potential red flags or gaps (e.g., career gaps, lack of specific details).
- Suggest general actionable steps to improve the candidate's marketability (e.g., "Build a portfolio", "Certifications in X").

---

### INPUTS:
CV:
{cv_text}

---

### OUTPUT SCHEMA (strict JSON only):

{{
  "content_improvements": {{
    "summary_critique": "Critique of the professional summary",
    "bullet_point_rewrites": [
        {{"original": "original bullet text", "improved": "rewritten bullet with strong verbs and metrics", "reason": "explanation"}}
    ],
    "quantification_suggestions": ["suggestion1", "suggestion2"]
  }},
  "structure_formatting": {{
    "layout_critique": "Comments on layout/structure",
    "clarity_suggestions": ["suggestion1", "suggestion2"],
    "buzzwords_to_remove": ["word1", "word2"]
  }},
  "strategic_advice": {{
    "core_strengths": ["strength1", "strength2"],
    "red_flags": ["flag1", "flag2"],
    "actionable_next_steps": ["step1", "step2"]
  }}
}}
"""


NO_JD_IMPROVEMENT_PROMPT = """You are an expert hiring evaluator. Your task is to analyze a Candidate CV and return a detailed scoring analysis.

Return ONLY valid JSON that strictly adheres to the schema provided at the end. Do NOT include explanations, apologies, or any prose outside of the JSON structure.

---

### INSTRUCTIONS & RUBRICS

**1. General Rules:**
- For each dimension, provide a score based on the provided CV and Job Description.
- For the `evidence` field in each subscore, you MUST provide an array of direct, concise quotes from the CV that justify your score.
- If no evidence can be found for a dimension, the score MUST be 0 and the `evidence` array must contain the single string "No evidence found.".

**2. PART 1: CV QUALITY (100 points total)**
Evaluate the CV's intrinsic quality, independent of the job description.
- ats_structure (10): Contact details are clear, sections are well-defined, bullets are easily parseable, dates are consistent.
- writing_clarity (15): Concise, uses active voice (e.g., "Led," "Developed"), parallel bullet structure, no typos or grammatical errors.
- quantified_impact (20): Uses specific metrics (% / $ / user numbers / latency reduction) to show the impact of actions.
- technical_depth (15): Mentions specific, non-generic tools/frameworks/architectures. Shows understanding of complex systems.
- projects_portfolio (10): Includes links to a portfolio, GitHub, or describes personal/open-source projects with outcomes.
- leadership_skills (10): Provides evidence of leading teams, mentoring others, project ownership, or significant cross-functional work.
- career_progression (10): Shows increasing responsibility over time. Timeline is clear and logical.
- consistency (10): Formatting, tone, and verb tenses are consistent throughout the document. No large, unexplained career gaps.

**3. PART 2: JOB MATCH (100 points total)**
Evaluate how well the CV matches the specific Job Description.
- hard_skills (35): Coverage of "must-have" technical skills, tools, and frameworks from the JD. Consider exact, alias (e.g., AWS vs. Amazon Web Services), and semantic matches.
- responsibilities (15): Overlap between the candidate's experience (verbs and outcomes) and the key responsibilities listed in the JD.
- domain_relevance (10): Match of the candidate's industry experience (e.g., FinTech, SaaS, AI) with the company's domain.
- seniority (10): Candidate's years of relevant experience vs. JD requirements (e.g., "5+ years").
- nice_to_haves (5): Coverage of optional skills or "bonus points" mentioned in the JD.
- education_certs (5): Match for required or preferred degrees and certifications.
- recent_achievements (10): Candidate's accomplishments in the last 1-2 roles directly align with the core needs of the job.
- constraints (10): Match on practical constraints like location, work authorization, or travel. If not mentioned, assume a match.

**4. PART 3: KEY TAKEAWAYS**
Based on your full analysis, identify critical highlights.
- red_flags: List any critical deal-breakers. A red flag is a clear mismatch on a non-negotiable requirement (e.g., JD requires US work authorization, CV states candidate needs sponsorship; JD requires a specific security clearance the candidate lacks).
- green_flags: List 2-3 standout qualifications that make the candidate exceptionally strong for this role.

---

### INPUTS:
CV:
{cv_text}

Job Description:
{jd_text}

---

### OUTPUT SCHEMA (strict JSON only):

{{
  "cv_quality": {{
    "overall_score": float,
    "subscores": [
      {{"dimension": "ats_structure", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "writing_clarity", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "quantified_impact", "score": float, "max_score": 20, "evidence": [string]}},
      {{"dimension": "technical_depth", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "projects_portfolio", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "leadership_skills", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "career_progression", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "consistency", "score": float, "max_score": 10, "evidence": [string]}}
    ]
  }},
  "jd_match": {{
    "overall_score": float,
    "subscores": [
      {{"dimension": "hard_skills", "score": float, "max_score": 35, "evidence": [string]}},
      {{"dimension": "responsibilities", "score": float, "max_score": 15, "evidence": [string]}},
      {{"dimension": "domain_relevance", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "seniority", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "nice_to_haves", "score": float, "max_score": 5, "evidence": [string]}},
      {{"dimension": "education_certs", "score": float, "max_score": 5, "evidence": [string]}},
      {{"dimension": "recent_achievements", "score": float, "max_score": 10, "evidence": [string]}},
      {{"dimension": "constraints", "score": float, "max_score": 10, "evidence": [string]}}
    ]
  }},
  "key_takeaways": {{
    "red_flags": [string],
    "green_flags": [string]
  }}
}}"""


RESUME_REWRITE_PROMPT = """You are an expert Professional Resume Writer. Your task is to rewrite a candidate's CV based on their original text and a set of requested improvements.

Return ONLY valid JSON that strictly adheres to the schema provided at the end. Do NOT include explanations, apologies, or any prose outside of the JSON structure.

---

### INSTRUCTIONS

**1. Consolidation & Rewriting**
- Merge the `Original CV Text` with the `Improvement Context`.
- If the improvement context asks to rewrite specific bullets (e.g., using STAR method), replace the old ones with the new, improved versions.
- If the improvement context provides a new summary, use it.
- Ensure the tone is professional, active, and consistent.

**2. Structure & Formatting**
- Organize the data into the strict JSON structure provided.
- Ensure `skills` are categorized logically (e.g., "Languages", "Frameworks", "Tools").
- Ensure `experience` is ordered reverse-chronologically (if dates are present).

**3. Accuracy**
- Do NOT hallucinate facts that are not in the original CV or the improvement context.
- You may rephrase and polish, but do not invent work history or degrees.

---

### INPUTS:

**Original CV Text:**
{cv_text}

**Improvement Instructions / Context:**
{improvement_context}

---

### OUTPUT SCHEMA (strict JSON only):

{{
  "personal_details": {{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "linkedin": "url",
    "github": "url",
    "location": "City, Country",
    "website": "url"
  }},
  "professional_summary": "Compelling summary text...",
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "dates": "Start - End",
      "location": "City",
      "description": ["Action-oriented bullet 1", "Action-oriented bullet 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "school": "University Name",
      "dates": "Year - Year",
      "location": "City",
      "details": ["Honors", "Relevant Coursework"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "role": "Role (optional)",
      "technologies": ["Tech A", "Tech B"],
      "link": "url",
      "description": ["Bullet 1", "Bullet 2"]
    }}
  ],
  "skills": {{
    "Languages": ["Python", "JavaScript"],
    "Frameworks": ["React", "Django"],
    "Tools": ["Docker", "Git"]
  }},
  "certifications": ["Cert Name, Issuer", "Cert Name 2"],
  "languages": ["English (Native)", "Spanish (Conversational)"],
  "achievements": ["Award 1", "Hackathon Win"]
}}
"""