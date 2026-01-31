# V2 Interview API Documentation (Gemini-Powered)

Complete API reference for `/v2/interview` endpoints with full request/response examples.

**Base URL:** `http://127.0.0.1:8000`  
**Technology:** Google Gemini 2.5 Pro  
**Features:** Resume + JD analysis, Audio transcription & voice analysis, Comprehensive evaluation reports

---

## Table of Contents
1. [Start Interview](#1-start-interview)
2. [Submit Answer](#2-submit-answer)
3. [Get Status](#3-get-status--current-question)
4. [Complete Interview](#4-complete-interview)
5. [Audio Support](#audio--voice-support)
6. [Known Issues](#known-issues--troubleshooting)

---

## 1) Start Interview

**`POST /v2/interview/start`**

**Description:**  
Initialize a new interview session by providing resume and job description (either as file uploads or text). The AI interviewer analyzes both documents and generates a contextual first question.

**Request Format:** `multipart/form-data`

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | form | Yes | Job position/role (e.g., "Software Engineer") |
| `company` | form | No | Company name (default: "the company") |
| `resume_file` | file | No* | Resume file (PDF/DOCX/TXT) |
| `jd_file` | file | No* | Job description file (PDF/DOCX/TXT) |
| `resume_text` | form | No* | Resume as plain text |
| `jd_text` | form | No* | JD as plain text |

*Either file or text must be provided for both resume and JD. Files take priority.

**cURL Examples:**

Using files:
```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Software Engineer" \
  -F "company=Acme Corp" \
  -F "resume_file=@/path/to/resume.pdf" \
  -F "jd_file=@/path/to/job_description.pdf"
```

Using text:
```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Data Scientist" \
  -F "company=Tech Startup" \
  -F "resume_text=John Doe, 5 years ML experience..." \
  -F "jd_text=Looking for experienced ML engineer..."
```

**Success Response (200):**
```json
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "active",
  "question": "Hello John, my name is Alex, and I'm a Senior Engineer at Acme Corp. I've reviewed your background in machine learning. Could you start by walking me through your most impactful ML project and the technologies you used?",
  "question_number": 1,
  "message": "Interview started successfully with Gemini AI"
}
```

**Error Responses:**

400 Bad Request - Missing required fields:
```json
{
  "detail": "Resume is required. Provide either resume_file or resume_text."
}
```

500 Internal Server Error - Model or parsing error:
```json
{
  "detail": "Error starting interview: 404 models/gemini-2.5-pro is not found..."
}
```

---

## 2) Submit Answer

**`POST /v2/interview/{session_id}/answer`**

**Description:**  
Submit candidate's answer as TEXT or AUDIO. Audio is automatically transcribed and analyzed for voice delivery metrics.

**Request Format:** `multipart/form-data`

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | form | No* | Typed/transcribed answer text |
| `answer_audio` | file | No* | Audio recording (WAV/MP3/M4A/etc.) |

*At least one must be provided. Audio takes priority and enables voice analysis.

**cURL Examples:**

Text answer:
```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/{SESSION_ID}/answer" \
  -F "answer=I built a recommendation system using Python and TensorFlow. We used collaborative filtering..."
```

Audio answer (with automatic transcription + voice analysis):
```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/{SESSION_ID}/answer" \
  -F "answer_audio=@/path/to/recording.wav"
```

**Success Response (200):**
```json
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "active",
  "question": "That's great. Can you explain how you handled cold-start problems in your recommendation system?",
  "question_number": 2
}
```

**Error Responses:**

400 Bad Request:
```json
{
  "detail": "Either 'answer' text or 'answer_audio' file is required"
}
```

404 Not Found:
```json
{
  "detail": "Session 039b4112-ce8a-4575-b137-64cec08bfabc not found"
}
```

500 Internal Server Error:
```json
{
  "detail": "Error processing answer: [error details]"
}
```

**Notes:**
- When audio is uploaded: transcription via Gemini + voice analysis (fluency, clarity, confidence, pace)
- Voice metrics influence follow-up questions and are included in final report

---

## 3) Get Status / Current Question

**`GET /v2/interview/{session_id}/status`**

**Description:**  
Retrieve current interview state without submitting an answer.

**cURL Example:**
```bash
curl "http://127.0.0.1:8000/v2/interview/{SESSION_ID}/status"
```

**Success Response (200):**
```json
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "active",
  "question": "Can you explain how you handled cold-start problems?",
  "question_number": 2,
  "history": [
    {
      "role": "interviewer",
      "content": "Hello John, could you walk me through your ML project?"
    },
    {
      "role": "candidate",
      "content": "I built a recommendation system...",
      "voice_metrics": {
        "rate_wpm": 125,
        "fluency_score": 7.2,
        "clarity_score": 7.5,
        "confidence_score": 6.8
      }
    },
    {
      "role": "interviewer",
      "content": "Can you explain how you handled cold-start problems?"
    }
  ]
}
```

**Error Response:**

404 Not Found:
```json
{
  "status": "not_found"
}
```

---

## 4) Complete Interview

**`POST /v2/interview/{session_id}/complete`**

**Description:**  
End the interview and receive comprehensive evaluation including voice analytics (if audio was used) and video analytics (sample data).

**Request Format:** `application/json`

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `final_notes` | string | No | Optional interviewer notes |

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/{SESSION_ID}/complete" \
  -H "Content-Type: application/json" \
  -d '{"final_notes":"Strong technical background"}'
```

**Success Response (200) - COMPLETE DETAILED REPORT:**
```json
{
  "session_id": "039b4112-ce8a-4575-b137-64cec08bfabc",
  "status": "completed",
  "interview_duration_minutes": 15,
  "total_questions": 5,
  "role": "Software Engineer",
  "company": "Acme Corp",
  
  "evaluation": {
    "overall_score": 8,
    "recommendation": "hire",
    "summary": "Strong candidate with excellent technical depth and clear communication. Demonstrated solid understanding of system design and practical ML experience.",
    "strengths": [
      "Deep knowledge of recommendation systems",
      "Clear and structured communication",
      "Practical problem-solving approach",
      "Strong understanding of scalability"
    ],
    "weaknesses": [
      "Could improve knowledge of distributed systems",
      "Limited experience with real-time ML pipelines"
    ],
    "technical_skills": {
      "score": 8,
      "assessment": "Demonstrated strong technical foundation with Python, TensorFlow, and system design. Showed practical knowledge of ML algorithms and deployment."
    },
    "communication_skills": {
      "score": 9,
      "assessment": "Excellent communicator. Explains complex concepts clearly, uses appropriate technical terminology, and structures answers logically."
    },
    "problem_solving": {
      "score": 8,
      "assessment": "Strong analytical thinking. Breaks down problems systematically and considers trade-offs. Good understanding of optimization."
    },
    "cultural_fit": {
      "score": 7,
      "assessment": "Shows collaborative mindset and eagerness to learn. Values code quality and best practices."
    },
    "experience_relevance": {
      "score": 9,
      "assessment": "Highly relevant background. Direct experience with technologies mentioned in JD. Projects align well with role requirements."
    },
    "detailed_feedback": "The candidate demonstrated exceptional technical knowledge throughout the interview. Their recommendation system project showcases strong ML fundamentals and practical deployment experience. Communication was clear and concise, with well-structured answers. Areas for growth include distributed systems architecture and real-time data pipelines, but overall this is a strong hire recommendation.",
    "improvement_areas": [
      "Deepen knowledge of distributed systems (Kafka, Spark)",
      "Gain experience with real-time ML serving",
      "Explore advanced feature engineering techniques"
    ],
    "key_highlights": [
      "Built production recommendation system serving 1M+ users",
      "Strong system design fundamentals",
      "Clear, professional communication style"
    ]
  },
  
  "video_analytics": {
    "confidence_score": 8.2,
    "eye_contact_percentage": 85,
    "posture_score": 8.5,
    "engagement_level": "high",
    "speech_pace": "moderate",
    "filler_words_count": 8,
    "smile_frequency": "appropriate",
    "facial_expressions": {
      "positive": 72,
      "neutral": 25,
      "stressed": 3
    },
    "body_language": {
      "open": 78,
      "closed": 12,
      "neutral": 10
    },
    "energy_level": "medium-high",
    "professionalism_score": 8.7,
    "note": "Sample data - video analysis requires video upload feature"
  },
  
  "voice_analytics": {
    "analysis_performed": true,
    "total_voice_samples": 3,
    "average_scores": {
      "fluency": 7.8,
      "clarity": 8.2,
      "confidence": 7.5,
      "pace": 7.3,
      "overall": 7.7
    },
    "speaking_rate_wpm": 132.5,
    "interpretation": {
      "fluency": "Good",
      "clarity": "Excellent",
      "confidence": "Good",
      "pace": "Good"
    },
    "detailed_scores": [
      {
        "rate_wpm": 128,
        "fluency_score": 7.5,
        "clarity_score": 8.0,
        "confidence_score": 7.2,
        "pace_score": 7.0,
        "total_score": 7.4,
        "pitch_mean_hz": 145.3,
        "pitch_std_hz": 22.1,
        "pause_ratio": 0.18
      },
      {
        "rate_wpm": 135,
        "fluency_score": 8.0,
        "clarity_score": 8.3,
        "confidence_score": 7.6,
        "pace_score": 7.5,
        "total_score": 7.9,
        "pitch_mean_hz": 148.7,
        "pitch_std_hz": 19.5,
        "pause_ratio": 0.15
      },
      {
        "rate_wpm": 134,
        "fluency_score": 7.9,
        "clarity_score": 8.3,
        "confidence_score": 7.7,
        "pace_score": 7.4,
        "total_score": 7.8,
        "pitch_mean_hz": 146.2,
        "pitch_std_hz": 21.0,
        "pause_ratio": 0.16
      }
    ]
  },
  
  "conversation": [
    {
      "role": "interviewer",
      "content": "Hello John, my name is Alex... Could you walk me through your ML project?"
    },
    {
      "role": "candidate",
      "content": "I built a recommendation system using Python and TensorFlow...",
      "voice_metrics": {
        "rate_wpm": 128,
        "fluency_score": 7.5,
        "clarity_score": 8.0,
        "confidence_score": 7.2
      }
    },
    {
      "role": "interviewer",
      "content": "Can you explain how you handled cold-start problems?"
    },
    {
      "role": "candidate",
      "content": "We used a hybrid approach combining content-based filtering..."
    }
  ],
  
  "metrics": {
    "response_quality": 8,
    "technical_depth": 8,
    "communication": 9,
    "overall_performance": 8
  }
}
```

**Error Responses:**

404 Not Found:
```json
{
  "detail": "Session 039b4112-ce8a-4575-b137-64cec08bfabc not found"
}
```

500 Internal Server Error - Evaluation parsing failed:
```json
{
  "detail": "Error completing interview: [error details]"
}
```

Note: If the Gemini model fails to return valid JSON, the system returns a fallback evaluation with the raw model output in `evaluation.detailed_feedback`.

---

## Audio / Voice Support

### ✅ Fully Implemented

The API natively supports audio uploads for candidate answers with automatic transcription and voice analysis.

### How It Works

1. **Upload Audio:** Use `answer_audio` parameter in `/v2/interview/{session_id}/answer`
2. **Transcription:** Gemini's multimodal API transcribes audio to text
3. **Voice Analysis:** VoiceAnalyzer computes:
   - **Fluency** (0-10): Speech smoothness, minimal stuttering/hesitation
   - **Clarity** (0-10): Articulation quality, pronunciation
   - **Confidence** (0-10): Vocal stability, pitch control
   - **Pace** (0-10): Speaking rate appropriateness (100-150 WPM ideal)
   - **Speaking Rate:** Words per minute
4. **Context Integration:** Metrics passed to Gemini for context-aware follow-ups
5. **Aggregation:** All voice scores averaged in final report

### Supported Audio Formats

- WAV (recommended)
- MP3
- M4A
- OGG
- FLAC

### Example Usage

```bash
# Record answer (use any recording app)
# Then upload:
curl -X POST "http://127.0.0.1:8000/v2/interview/{SESSION_ID}/answer" \
  -F "answer_audio=@recording.wav"
```

### Voice Metrics Output

Each audio answer produces:
```json
{
  "rate_wpm": 132,
  "fluency_score": 7.8,
  "clarity_score": 8.2,
  "confidence_score": 7.5,
  "pace_score": 7.3,
  "total_score": 7.7,
  "pitch_mean_hz": 146.2,
  "pitch_std_hz": 21.0,
  "pause_ratio": 0.16
}
```

### Final Report Includes

- **Average Scores:** Mean across all audio answers
- **Interpretation:** Qualitative ratings (Excellent/Good/Needs improvement)
- **Detailed Breakdown:** Per-answer voice metrics
- **Speaking Rate:** Overall WPM average

---

## Known Issues & Troubleshooting

### Model Errors (404)

**Problem:** `models/gemini-1.5-pro is not found for API version v1beta`

**Solution:**
- The code uses `gemini-2.5-pro` which is available in your account
- To verify available models, run:
  ```bash
  python debug_gemini_models.py
  ```
- Update `interview/gemini_interviewer.py` if needed

### MongoDB Connection Failures

**Problem:** `ServerSelectionTimeoutError: No replica set members match selector "Primary()"`

**Solution:**
- V2 endpoints work WITHOUT MongoDB (use in-memory sessions)
- Server will start with warning but endpoints function normally
- Check MongoDB connection string in `.env` if you need DB features

### Swagger UI Shows Text Fields Instead of File Upload

**Problem:** OpenAPI not regenerated after code changes

**Solution:**
- Restart the server: `uvicorn apps.api.app:app --reload`
- Clear browser cache
- Check `/openapi.json` endpoint directly

### MediaPipe Initialization Warnings

**Problem:** Large MediaPipe proto graph logs on startup

**Solution:**
- These are harmless verbose logs from MediaPipe
- Video analysis falls back to sample data if MediaPipe unavailable
- To suppress, set logging level to WARNING in code

### Audio Processing Errors

**Problem:** Voice analysis fails or returns empty metrics

**Solution:**
- Ensure audio file is valid and not corrupted
- Check file size (large files may timeout)
- Verify audio has actual speech content (not silence)
- Use WAV format for best compatibility

---

## Quick Start Example

Complete interview flow:

```bash
# 1. Start interview
SESSION=$(curl -s -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Software Engineer" \
  -F "company=TechCorp" \
  -F "resume_file=@resume.pdf" \
  -F "jd_file=@jd.pdf" | jq -r '.session_id')

echo "Session: $SESSION"

# 2. Answer with audio
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/answer" \
  -F "answer_audio=@answer1.wav"

# 3. Answer with text
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/answer" \
  -F "answer=I have 5 years of experience with microservices..."

# 4. Check status
curl "http://127.0.0.1:8000/v2/interview/$SESSION/status" | jq .

# 5. Complete and get report
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/complete" \
  -H "Content-Type: application/json" \
  -d '{}' | jq . > interview_report.json
```

---

## API Summary

| Endpoint | Method | Purpose | Audio Support |
|----------|--------|---------|---------------|
| `/v2/interview/start` | POST | Initialize session | ❌ |
| `/v2/interview/{id}/answer` | POST | Submit answer | ✅ Yes (multipart) |
| `/v2/interview/{id}/status` | GET | Get current state | ❌ |
| `/v2/interview/{id}/complete` | POST | End & get report | ❌ |

---

## Support

For issues or questions:
- Check server logs for detailed error messages
- Verify Gemini API key in `.env`
- Test with sample text inputs before using audio
- Review `docs/V2_INTERVIEW_API_COMPLETE.md` for full examples
