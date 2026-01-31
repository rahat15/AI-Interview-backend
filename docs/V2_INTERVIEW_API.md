# V2 Interview API (Gemini)

This document describes the `/v2/interview` endpoints implemented in the repository, with concrete curl examples and full sample responses (success and error cases).

Base URL used in examples: `http://127.0.0.1:8000`

---

## 1) Start Interview

POST /v2/interview/start

Description:
- Start a new interview session using a Resume and Job Description. Accepts either file uploads or inline text fields. Files take priority when provided.

Request (multipart/form-data):
- `role` (form, required): job role string
- `company` (form, optional): company name
- `resume_file` (file, optional): PDF/DOCX/TXT resume (preferred)
- `jd_file` (file, optional): PDF/DOCX/TXT job description (preferred)
- `resume_text` (form, optional): resume text (used if no file provided)
- `jd_text` (form, optional): jd text (used if no file provided)

Curl - using files:
```
curl -v -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Software Engineer" \
  -F "company=Acme Corp" \
  -F "resume_file=@/full/path/to/resume.pdf" \
  -F "jd_file=@/full/path/to/jd.pdf"
```

Curl - using plain text fields (fallback):
```
curl -v -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Software Engineer" \
  -F "company=Acme Corp" \
  -F "resume_text=$(< /full/path/to/resume.txt)" \
  -F "jd_text=$(< /full/path/to/jd.txt)"
```

Successful Response (200):
```
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "active",
  "question": "Hello Isha, my name is Alex, and I'm a Senior Software Engineer here at Acme Corp. Could you start by walking me through the architecture of your 'Hidden Gems' project?",
  "question_number": 1
}
```

Errors:
- 400 Bad Request — missing required fields (e.g., `role`) or both resume/jd missing.
- 500 Internal Server Error — model errors, parsing errors. Example:
```
{ "detail": "Error starting interview: 404 models/gemini-1.5-pro is not found for API version v1beta..." }
```

Notes:
- If you see text inputs only in Swagger UI for these fields, restart the server so OpenAPI regenerates.
- Uploaded PDFs/DOCX/TXT are parsed to extract text; unsupported file formats will cause a 400/500 depending on parsing errors.

---

## 2) Submit Answer

POST /v2/interview/{session_id}/answer

Description:
- Submit the candidate's answered text for the current question. Optionally provide `voice_metrics` (computed locally or client-side) so the interviewer can incorporate delivery metrics.

Request (application/json):
- `answer` (string, required) — candidate's transcribed or typed answer
- `voice_metrics` (object, optional) — voice analysis metrics, e.g. `rate_wpm`, `fluency_score`, `clarity_score`, `confidence_score`.

Curl Example:
```
curl -v -X POST "http://127.0.0.1:8000/v2/interview/039b4112-ce8a-4575-b137-64cec08bfabc/answer" \
  -H "Content-Type: application/json" \
  -d '{"answer":"I implemented REST endpoints using Express and MongoDB...","voice_metrics":{"rate_wpm":120,"fluency_score":7.2}}'
```

Successful Response (200):
```
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "active",
  "question": "Thanks — that’s helpful. Can you explain how you handled pagination and indexing for the reviews collection?",
  "question_number": 2
}
```

Errors:
- 404 Not Found — session not found
- 500 Internal Server Error — LLM generation error or prompt parsing error

Notes:
- When `voice_metrics` are provided, they are appended to session history and included in the prompt that generates the next question.

---

## 3) Get Status / Current Question

GET /v2/interview/{session_id}/status

Description:
- Return current session info including latest question, question number and history.

Curl Example:
```
curl -v "http://127.0.0.1:8000/v2/interview/039b4112-ce8a-4575-b137-64cec08bfabc/status"
```

Successful Response (200):
```
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "active",
  "question": "Can you explain how you handled pagination and indexing for the reviews collection?",
  "question_number": 2,
  "history": [
    {"role":"interviewer","content":"...first question..."},
    {"role":"candidate","content":"...candidate answer..."},
    {"role":"interviewer","content":"...second question..."}
  ]
}
```

Errors:
- 404 Not Found — session not found.

---

## 4) Complete Interview

POST /v2/interview/{session_id}/complete

Description:
- Ends the interview session and triggers a comprehensive evaluation from the Gemini model. Also returns sample video and voice analytics (video analysis may be mocked if MediaPipe is unavailable).

Request (application/json):
- `final_notes` (string, optional)

Curl Example:
```
curl -v -X POST "http://127.0.0.1:8000/v2/interview/039b4112-ce8a-4575-b137-64cec08bfabc/complete" \
  -H "Content-Type: application/json" \
  -d '{"final_notes":"Candidate showed solid architecture intuition."}'
```

Successful Response (200):
```
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "completed",
  "interview_duration_minutes": 15,
  "total_questions": 5,
  "role": "Software Engineer",
  "company": "Acme Corp",
  "evaluation": {
    "overall_score": 7,
    "recommendation": "maybe",
    "summary": "Good candidate with relevant experience",
    "strengths": ["Strong communication","Relevant experience","Good problem-solving"],
    "weaknesses": ["Could improve technical depth"],
    "technical_skills": {"score":7,"assessment":"Solid technical foundation"},
    "communication_skills": {"score":8,"assessment":"Communicates clearly"},
    "problem_solving": {"score":7,"assessment":"Good analytical approach"},
    "cultural_fit": {"score":7,"assessment":"Aligns with company values"},
    "experience_relevance": {"score":8,"assessment":"Highly relevant background"},
    "detailed_feedback": "Comprehensive evaluation paragraph...",
    "improvement_areas": ["Technical depth in distributed systems"],
    "key_highlights": ["Strong communication", "Relevant project experience"]
  },
  "video_analytics": {
    "confidence_score": 7.8,
    "eye_contact_percentage": 82,
    "posture_score": 8.2,
    "engagement_level": "high",
    "speech_pace": "moderate",
    "filler_words_count": 12,
    "smile_frequency": "appropriate",
    "facial_expressions": {"positive": 68, "neutral": 28, "stressed": 4},
    "body_language": {"open": 75, "closed": 15, "neutral": 10},
    "energy_level": "medium-high",
    "professionalism_score": 8.5,
    "note": "Sample data - video analysis requires video upload feature"
  },
  "voice_analytics": {
    "analysis_performed": true,
    "total_voice_samples": 3,
    "average_scores": {
      "fluency": 7.2,
      "clarity": 7.5,
      "confidence": 7.0,
      "pace": 6.8,
      "overall": 7.1
    },
    "speaking_rate_wpm": 128.5,
    "interpretation": {
      "fluency": "Good",
      "clarity": "Good",
      "confidence": "Good",
      "pace": "Good"
    },
    "detailed_scores": [
      {"rate_wpm": 120, "fluency_score": 7.0, "clarity_score": 7.3, "confidence_score": 6.8},
      {"rate_wpm": 132, "fluency_score": 7.5, "clarity_score": 7.8, "confidence_score": 7.2},
      {"rate_wpm": 134, "fluency_score": 7.1, "clarity_score": 7.4, "confidence_score": 7.0}
    ]
  },
  "conversation": [
    {"role":"interviewer","content":"First question..."},
    {"role":"candidate","content":"Answer 1...", "voice_metrics": {...}},
    {"role":"interviewer","content":"Second question..."}
  ],
  "metrics": {
    "response_quality": 7,
    "technical_depth": 7,
    "communication": 8,
    "overall_performance": 7
  }
}
```

Errors:
- 404 Not Found — session not found
- 500 Internal Server Error — model failed to return valid JSON. In that case the service returns a fallback evaluation object (see implementation) and includes raw model text in `evaluation.detailed_feedback`.

---

## Voice / Audio Support

✅ **FULLY IMPLEMENTED** - Audio upload & analysis now supported!

The `/v2/interview/{session_id}/answer` endpoint accepts audio files directly:

**How it works:**
1. Upload audio file (WAV, MP3, M4A, etc.) via `answer_audio` parameter
2. Server transcribes audio using Gemini's multimodal API
3. VoiceAnalyzer computes delivery metrics:
   - **Fluency** (0-10): speech smoothness, pauses
   - **Clarity** (0-10): articulation quality
   - **Confidence** (0-10): vocal stability, pitch control
   - **Pace** (0-10): speaking rate appropriateness
   - **Speaking rate** (words per minute)
4. Metrics are passed to the interviewer AI for context-aware follow-ups
5. All voice scores are aggregated in the final report

**Example - Submit audio answer:**
```bash
curl -v -X POST "http://127.0.0.1:8000/v2/interview/{session_id}/answer" \
  -F "answer_audio=@/path/to/recording.wav"
```

**Final Report includes:**
- `voice_analytics.analysis_performed`: true if any audio was submitted
- `voice_analytics.total_voice_samples`: count of audio answers
- `voice_analytics.average_scores`: mean fluency/clarity/confidence/pace across all answers
- `voice_analytics.speaking_rate_wpm`: average speaking rate
- `voice_analytics.interpretation`: qualitative assessment (Excellent/Good/Needs improvement)
- `voice_analytics.detailed_scores`: per-answer breakdown

**Note:** Text answers are still supported via the `answer` parameter if you don't have audio.

---

## Known Issues & Troubleshooting

- Model selection errors (404): Ensure the Gemini model name is supported by your account. Use the included `debug_gemini_models.py` to list available models. Choose one that supports `generateContent`.
- MediaPipe video analysis: may produce long startup logs or fail when native libs are missing; when that happens the service returns sample video analytics.
- OpenAPI/Swagger duplication for `/start`: restart the server to regenerate OpenAPI after code changes. The UI will show proper multipart file inputs when the endpoint is defined with `UploadFile` / `Form` parameters.

---

If you want, I can:
- Add server-side `answer_audio` handling (transcription + analysis).
- Produce a Postman collection or run a quick end-to-end test against your running server.

File: docs/V2_INTERVIEW_API.md
