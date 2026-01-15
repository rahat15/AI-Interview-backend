# API Structure - After Cleanup

```
AI Interview Coach API (v1.0.0)
│
├── /healthz (Health Check)
│
└── /v1/ (Versioned API)
    │
    ├── /cv/ (CV Evaluation)
    │   ├── POST /score              - Score CV quality only
    │   ├── POST /fit-index          - Score CV + JD fit
    │   └── POST /improvement        - Generate CV improvements
    │
    ├── /upload/ (File Upload & Processing)
    │   ├── POST /cv_evaluate        - Upload CV + optional JD for evaluation
    │   └── POST /cv_improvement     - Upload CV + JD for improvement suggestions
    │
    ├── /evaluation/ (Direct Evaluation)
    │   └── [Evaluation endpoints]
    │
    ├── /sessions/ (Session Management)
    │   ├── POST   /                 - Create new session
    │   ├── GET    /                 - List all sessions
    │   ├── GET    /{id}             - Get session details
    │   ├── GET    /{id}/next-question - Get next question
    │   ├── POST   /{id}/answer      - Submit text answer
    │   ├── GET    /{id}/report      - Get session report
    │   ├── DELETE /{id}             - Delete session
    │   ├── POST   /{id}/jd-text     - Add JD text to session
    │   ├── GET    /resume/{id}      - Get resume details
    │   ├── GET    /debug/resumes    - Debug: List all resumes
    │   └── GET    /debug/resume/{id} - Debug: Get resume details
    │
    ├── /jd/ (Job Description Management)
    │   ├── POST   /upload           - Upload JD file
    │   ├── GET    /                 - List all JDs
    │   ├── GET    /{id}             - Get JD by ID
    │   └── DELETE /{id}             - Delete JD
    │
    ├── /audio/ (Audio Processing)
    │   ├── POST /{session_id}/answer - Submit audio answer (with STT + voice analysis)
    │   └── POST /analyze            - Analyze audio only (no session)
    │
    └── /interview/ (Live Interview Flow)
        ├── POST /start              - Start interview session
        ├── POST /answer             - Submit audio answer
        ├── GET  /debug/sessions     - Debug: List active sessions
        ├── GET  /state/{user_id}/{session_id} - Get interview state
        ├── GET  /sessions/{user_id} - Get user's sessions
        └── GET  /report/{user_id}/{session_id} - Get interview report
```

## Key Improvements

### ✅ No Duplicates
- Removed duplicate `uploads.py` router
- Removed duplicate audio answer endpoint from sessions
- Removed duplicate interview router registration

### ✅ Consistent Prefixes
- All endpoints use `/v1` prefix for versioning
- Clear separation of concerns by functional area

### ✅ Better Organization
- CV operations: `/v1/cv/*`
- File uploads: `/v1/upload/*`
- Session management: `/v1/sessions/*`
- Audio processing: `/v1/audio/*`
- Live interviews: `/v1/interview/*`
- JD management: `/v1/jd/*`

### ✅ Clear Swagger Documentation
- Each endpoint group has a clear tag
- No confusion from duplicate endpoints
- Easy to navigate and test

## Usage Examples

### 1. Evaluate CV Quality
```bash
curl -X POST "http://localhost:8000/v1/cv/score" \
  -H "Content-Type: application/json" \
  -d '{"cv_text": "Your CV text here"}'
```

### 2. Upload CV for Evaluation
```bash
curl -X POST "http://localhost:8000/v1/upload/cv_evaluate" \
  -F "file=@cv.pdf" \
  -F "jd_text=Job description here"
```

### 3. Create Interview Session
```bash
curl -X POST "http://localhost:8000/v1/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Senior Backend Engineer",
    "industry": "Technology",
    "company": "TechCorp"
  }'
```

### 4. Submit Audio Answer
```bash
curl -X POST "http://localhost:8000/v1/audio/{session_id}/answer" \
  -F "question_id=123" \
  -F "audio_file=@answer.mp3"
```

### 5. Start Live Interview
```bash
curl -X POST "http://localhost:8000/v1/interview/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "role_title": "Backend Engineer",
    "company_name": "TechCorp",
    "industry": "Technology"
  }'
```
