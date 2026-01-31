# Gemini Interview API Documentation

## Audio Evaluation in Gemini Module

The Gemini Interview API evaluates audio responses through a sophisticated multi-layered approach:

### Audio Processing Pipeline

1. **Audio Transcription**: Uses Gemini's multimodal capabilities to convert speech to text
2. **Voice Metrics Analysis**: Extracts speaking characteristics including:
   - Speaking rate (words per minute)
   - Fluency score (0-10)
   - Confidence score (0-10) 
   - Clarity score (0-10)
3. **Contextual Integration**: Voice metrics are fed into Gemini's evaluation prompt to influence communication skills assessment

### Voice Analysis Integration

When audio is submitted, the system:
- Transcribes audio using `transcribe_audio()` method
- Analyzes voice characteristics via `voice_metrics` parameter
- Incorporates voice data into interview flow with context like:
  ```
  [VOICE ANALYSIS DATA]
  The candidate answered via VOICE.
  - Speaking Rate: 150 words/min
  - Fluency Score: 8.5/10
  - Confidence Score: 7.2/10
  - Clarity: 9.1/10
  (Consider these metrics when evaluating communication skills)
  ```

---

## API Endpoints

### Base URL: `http://localhost:8000`

---

## 1. Interview Management (V2 - Gemini Powered)

### Start Interview
**POST** `/v2/interview/start`

Start a new interview session with resume and job description.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `role` (string, required): Job role/position
- `company` (string, optional): Company name (default: "the company")
- `resume_text` (string, optional): Resume as text
- `jd_text` (string, optional): Job description as text
- `resume_file` (file, optional): Resume file (PDF, DOCX, TXT)
- `jd_file` (file, optional): JD file (PDF, DOCX, TXT)

**Response** `200 OK`:
```json
{
  "session_id": "uuid-string",
  "status": "active",
  "question": "Hi! I'm Alex, a Senior Software Engineer at TechCorp. I'm excited to learn more about your background. Let's start with you telling me about yourself and what drew you to apply for this Senior Backend Engineer position.",
  "question_number": 1,
  "message": "Interview started successfully with Gemini AI"
}
```

**Error Responses**:
- `400 Bad Request`: Missing resume or JD
- `500 Internal Server Error`: Processing error

---

### Submit Answer
**POST** `/v2/interview/{session_id}/answer`

Submit candidate's answer and receive next question.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "answer": "I'm a passionate software engineer with 5 years of experience in backend development..."
}
```

**Response** `200 OK`:
```json
{
  "session_id": "uuid-string",
  "status": "active",
  "question": "That's great background! I noticed you mentioned experience with microservices. Can you walk me through a specific project where you designed or implemented a microservices architecture?",
  "question_number": 2
}
```

**Error Responses**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Processing error

---

### Complete Interview
**POST** `/v2/interview/{session_id}/complete`

End interview and get comprehensive evaluation.

**Response** `200 OK`:
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "interview_duration_minutes": 15,
  "total_questions": 5,
  "role": "Senior Backend Engineer",
  "company": "TechCorp",
  "evaluation": {
    "overall_score": 8.2,
    "recommendation": "hire",
    "summary": "Strong candidate with excellent technical skills and clear communication. Shows deep understanding of backend systems and good problem-solving approach.",
    "strengths": [
      "Strong technical foundation in backend development",
      "Clear and articulate communication",
      "Good problem-solving methodology"
    ],
    "weaknesses": [
      "Could provide more specific metrics in examples",
      "Limited leadership experience mentioned"
    ],
    "technical_skills": {
      "score": 8.5,
      "assessment": "Demonstrates solid understanding of backend architecture, databases, and system design principles"
    },
    "communication_skills": {
      "score": 8.0,
      "assessment": "Communicates technical concepts clearly and concisely"
    },
    "problem_solving": {
      "score": 8.2,
      "assessment": "Shows systematic approach to problem-solving with good analytical thinking"
    },
    "cultural_fit": {
      "score": 7.8,
      "assessment": "Aligns well with company values and demonstrates collaborative mindset"
    },
    "experience_relevance": {
      "score": 8.7,
      "assessment": "Highly relevant experience that directly matches job requirements"
    },
    "detailed_feedback": "The candidate demonstrated strong technical competency throughout the interview...",
    "improvement_areas": [
      "Provide more quantifiable achievements",
      "Develop leadership examples",
      "Practice system design scenarios"
    ],
    "key_highlights": [
      "5+ years backend development experience",
      "Strong microservices architecture knowledge",
      "Excellent communication skills"
    ]
  },
  "video_analytics": {
    "confidence_score": 7.8,
    "eye_contact_percentage": 82,
    "posture_score": 8.2,
    "engagement_level": "high",
    "speech_pace": "moderate",
    "filler_words_count": 12,
    "smile_frequency": "appropriate",
    "facial_expressions": {
      "positive": 68,
      "neutral": 28,
      "stressed": 4
    },
    "body_language": {
      "open": 75,
      "closed": 15,
      "neutral": 10
    },
    "energy_level": "medium-high",
    "professionalism_score": 8.5
  },
  "conversation": [
    {
      "role": "interviewer",
      "content": "Hi! I'm Alex, a Senior Software Engineer..."
    },
    {
      "role": "candidate",
      "content": "I'm a passionate software engineer..."
    }
  ],
  "metrics": {
    "response_quality": 8.2,
    "technical_depth": 8.5,
    "communication": 8.0,
    "overall_performance": 8.2
  }
}
```

**Error Responses**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Processing error

---

### Get Interview Status
**GET** `/v2/interview/{session_id}/status`

Get current interview session status.

**Response** `200 OK`:
```json
{
  "session_id": "uuid-string",
  "status": "active",
  "question_number": 3,
  "role": "Senior Backend Engineer",
  "company": "TechCorp"
}
```

**Error Responses**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Processing error

---

## 2. Audio/Video Processing

### Submit Audio/Video Answer
**POST** `/audio/{session_id}/answer`

Submit audio or video answer with advanced analysis.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `question_id` (string, required): Question identifier
- `audio_file` (file, optional): Audio file
- `video_file` (file, optional): Video file

**Response** `200 OK`:
```json
{
  "evaluation": {
    "technical_score": 8.5,
    "communication_score": 7.8,
    "overall_score": 8.1
  },
  "technical": {
    "depth": 8.2,
    "accuracy": 8.8,
    "completeness": 8.0
  },
  "communication": {
    "clarity": 8.5,
    "structure": 7.5,
    "engagement": 8.0
  },
  "voice_analysis": {
    "rate_wpm": 145,
    "fluency_score": 8.2,
    "confidence_score": 7.8,
    "clarity_score": 8.5,
    "filler_words": 8,
    "pause_analysis": {
      "appropriate_pauses": 12,
      "excessive_pauses": 2
    }
  },
  "video_analysis": {
    "eye_contact_score": 8.1,
    "posture_score": 7.9,
    "facial_expressions": {
      "confidence": 8.0,
      "engagement": 8.2,
      "stress_indicators": 2.1
    },
    "gesture_analysis": {
      "appropriate_gestures": 15,
      "nervous_gestures": 3
    }
  },
  "next_question": "Great explanation! Now let's dive deeper into database optimization...",
  "state": {
    "completed": false,
    "progress": 60
  }
}
```

**Error Responses**:
- `400 Bad Request`: No audio/video file provided
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Processing error

---

### Analyze Audio/Video Only
**POST** `/audio/analyze`

Analyze audio/video characteristics without session context.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `audio_file` (file, optional): Audio file
- `video_file` (file, optional): Video file

**Response** `200 OK`:
```json
{
  "transcribed_text": "I believe the best approach to handle this scenario would be to implement a caching layer...",
  "voice_analysis": {
    "rate_wpm": 152,
    "fluency_score": 8.7,
    "confidence_score": 8.1,
    "clarity_score": 9.0,
    "tone_analysis": {
      "professional": 8.5,
      "enthusiastic": 7.2,
      "nervous": 2.1
    },
    "speech_patterns": {
      "filler_words": 6,
      "repetitions": 2,
      "incomplete_sentences": 1
    }
  },
  "video_analysis": {
    "confidence_indicators": {
      "eye_contact": 8.3,
      "posture": 8.0,
      "hand_gestures": 7.8
    },
    "engagement_metrics": {
      "facial_animation": 7.9,
      "head_movement": 8.1,
      "overall_energy": 8.2
    },
    "professionalism": {
      "appearance": 9.0,
      "background": 8.5,
      "lighting": 7.8
    }
  }
}
```

**Error Responses**:
- `400 Bad Request`: No file provided
- `500 Internal Server Error`: Processing error

---

## 3. Session Management (Legacy)

### Create Session
**POST** `/sessions/`

Create traditional interview session.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "role": "Senior Backend Engineer",
  "industry": "Technology",
  "company": "TechCorp Inc",
  "cv_file_id": "resume-uuid",
  "jd_text": "We are looking for a senior backend engineer..."
}
```

**Response** `201 Created`:
```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "role": "Senior Backend Engineer",
  "industry": "Technology",
  "company": "TechCorp Inc",
  "status": "active",
  "plan_json": {
    "jd_text": "We are looking for..."
  },
  "cv_file_id": "resume-uuid",
  "jd_file_id": null,
  "current_question_index": 0,
  "total_questions": 10,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "completed_at": null
}
```

**Error Responses**:
- `404 Not Found`: Resume not found
- `500 Internal Server Error`: Creation failed

---

### Get Session
**GET** `/sessions/{session_id}`

Retrieve session details.

**Response** `200 OK`:
```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "role": "Senior Backend Engineer",
  "industry": "Technology",
  "company": "TechCorp Inc",
  "status": "active",
  "plan_json": {},
  "cv_file_id": "resume-uuid",
  "jd_file_id": null,
  "current_question_index": 2,
  "total_questions": 10,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "completed_at": null
}
```

**Error Responses**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Retrieval error

---

### List Sessions
**GET** `/sessions/`

Get all sessions.

**Response** `200 OK`:
```json
[
  {
    "id": "session-uuid-1",
    "user_id": "user-uuid",
    "role": "Senior Backend Engineer",
    "industry": "Technology",
    "company": "TechCorp Inc",
    "status": "completed",
    "current_question_index": 10,
    "total_questions": 10,
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T11:00:00Z"
  }
]
```

---

### Get Next Question
**GET** `/sessions/{session_id}/next-question`

Get next interview question.

**Response** `200 OK`:
```json
{
  "question_id": "question-uuid",
  "text": "Tell me about a challenging technical problem you solved recently",
  "competency": "technical",
  "difficulty": "medium",
  "meta": {}
}
```

**Error Responses**:
- `404 Not Found`: Session completed or not found
- `500 Internal Server Error`: Question generation error

---

### Submit Answer (Legacy)
**POST** `/sessions/{session_id}/answer`

Submit answer to current question.

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "question_id": "question-uuid",
  "session_id": "session-uuid",
  "text": "I recently worked on optimizing our database queries..."
}
```

**Response** `200 OK`:
```json
{
  "message": "Answer submitted successfully",
  "answer_id": "answer-uuid",
  "next_question_index": 3,
  "session_completed": false
}
```

**Error Responses**:
- `400 Bad Request`: No pending question
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Submission error

---

### Get Session Report
**GET** `/sessions/{session_id}/report`

Generate session evaluation report.

**Response** `200 OK`:
```json
{
  "id": "report-uuid",
  "session_id": "session-uuid",
  "report_json": {
    "summary": "Great performance overall",
    "overall_score": 85.0,
    "competency_breakdown": {
      "technical": 4.2,
      "behavioral": 4.0,
      "communication": 4.1
    }
  },
  "summary": "Great performance overall with strong technical skills",
  "overall_score": 85.0,
  "strengths": [
    "Technical expertise",
    "Clear communication",
    "Problem-solving"
  ],
  "areas_for_improvement": [
    "Leadership examples",
    "More specific metrics"
  ],
  "recommendations": [
    "Practice STAR method",
    "Prepare leadership stories"
  ],
  "created_at": "2024-01-15T11:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Report generation error

---

### Delete Session
**DELETE** `/sessions/{session_id}`

Delete interview session.

**Response** `200 OK`:
```json
{
  "message": "Session deleted successfully"
}
```

**Error Responses**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Deletion error

---

## 4. File Upload & Processing

### CV Evaluation
**POST** `/upload/cv_evaluate`

Upload and evaluate CV with optional JD.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (file, required): CV file (PDF, DOC, DOCX, TXT, RTF, HTML, ODT, images)
- `jd_text` (string, optional): Job description text
- `jd_file` (file, optional): JD file

**Response** `200 OK`:
```json
{
  "overall_score": 8.2,
  "sections": {
    "contact_info": {
      "score": 9.0,
      "feedback": "Complete contact information provided"
    },
    "experience": {
      "score": 8.5,
      "feedback": "Strong relevant experience with good progression"
    },
    "skills": {
      "score": 8.0,
      "feedback": "Good technical skills alignment with requirements"
    },
    "education": {
      "score": 7.8,
      "feedback": "Relevant educational background"
    }
  },
  "strengths": [
    "Strong technical background",
    "Relevant industry experience",
    "Clear career progression"
  ],
  "improvements": [
    "Add more quantifiable achievements",
    "Include relevant certifications",
    "Improve formatting consistency"
  ],
  "jd_match": {
    "score": 8.3,
    "matched_skills": ["Python", "AWS", "Docker", "Kubernetes"],
    "missing_skills": ["GraphQL", "Terraform"]
  }
}
```

**Error Responses**:
- `400 Bad Request`: Unsupported file type or evaluation failed
- `500 Internal Server Error`: Processing error

---

### CV Improvement
**POST** `/upload/cv_improvement`

Generate improved resume with JD matching.

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (file, required): CV file
- `jd_text` (string, required): Job description text
- `jd_file` (file, optional): JD file (alternative to text)

**Response** `200 OK`:
```json
{
  "improved_resume": {
    "content": "JOHN DOE\nSenior Backend Engineer\n\nPROFESSIONAL SUMMARY\nResults-driven Senior Backend Engineer with 5+ years...",
    "improvements_made": [
      "Added quantifiable achievements",
      "Optimized keywords for ATS",
      "Improved technical skills section",
      "Enhanced project descriptions"
    ]
  },
  "benchmark_analysis": {
    "industry_comparison": {
      "experience_level": "Above Average",
      "skill_relevance": "High",
      "achievement_quantification": "Improved"
    },
    "ats_score": 8.7,
    "keyword_optimization": 8.5
  },
  "cover_letter": {
    "content": "Dear Hiring Manager,\n\nI am writing to express my strong interest in the Senior Backend Engineer position...",
    "key_points": [
      "Highlighted relevant experience",
      "Addressed specific JD requirements",
      "Demonstrated value proposition"
    ]
  },
  "recommendations": [
    "Consider adding cloud certifications",
    "Include more leadership examples",
    "Quantify team size and project impact"
  ]
}
```

**Error Responses**:
- `400 Bad Request`: JD required or improvement failed
- `500 Internal Server Error`: Processing error

---

## 5. Health & Monitoring

### Health Check
**GET** `/healthz`

System health status.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "gemini_api": "healthy",
    "file_storage": "healthy"
  }
}
```

---

## Error Handling

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "detail": "Specific error message describing what went wrong",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred",
  "error_code": "INTERNAL_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Authentication

Most endpoints require JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -X GET http://localhost:8000/sessions/
```

---

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **File uploads**: 10 requests per minute per IP
- **Interview sessions**: 5 concurrent sessions per user

---

## Supported File Formats

### Resume/CV Files
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Plain text (.txt)
- Rich Text Format (.rtf)
- HTML (.html, .htm)
- OpenDocument Text (.odt)
- Images with OCR (.png, .jpg, .jpeg, .tiff)

### Audio Files
- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- FLAC (.flac)

### Video Files
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- WebM (.webm)