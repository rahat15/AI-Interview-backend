# API curl Examples — Interview Coach Backend

**Base URL:**  
```
http://localhost:3000
```

---

# 🧩 Interview API (No Prefix)

## ▶️ Start Interview Session
```bash
curl -X POST "http://localhost:3000/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "session_id": "session-123",
    "role_title": "Backend Engineer",
    "company_name": "Acme",
    "industry": "Software",
    "jd": "Design microservices in Python",
    "cv": "Experienced Python backend engineer",
    "round_type": "full"
  }'
```

## ▶️ Submit Voice Answer (AUDIO ONLY)
```bash
curl -X POST "http://localhost:3000/answer" \
  -F "user_id=user-123" \
  -F "session_id=session-123" \
  -F "audio_file=@/path/to/audio.wav"
```

**⚠️ Note: Only audio files accepted - no text input**

## ▶️ Get Current State
```bash
curl "http://localhost:3000/state/user-123/session-123"
```

## ▶️ Get Final Report
```bash
curl "http://localhost:3000/report/user-123/session-123"
```

## ▶️ List All Interview Sessions (for a user)
```bash
curl "http://localhost:3000/sessions/user-123"
```

---

# 📄 CV Evaluation (`/v1/cv`)

## ▶️ Score CV Quality
```bash
curl -X POST "http://34.27.237.113:8000/v1/cv/score" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "<raw resume text>"
  }'
```

## ▶️ Fit-Index (CV + JD)
```bash
curl -X POST "http://34.27.237.113:8000/v1/cv/fit-index" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "<resume text>",
    "jd_text": "<job description text>"
  }'
```

## ▶️ Generate CV Improvement Suggestions
```bash
curl -X POST "http://34.27.237.113:8000/v1/cv/improvement" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "<resume text>",
    "jd_text": "<job description>"
  }'
```

---

# 📤 Upload-Based CV Evaluation (`/upload`)

## ▶️ Upload CV for Evaluation
```bash
curl -X POST "http://34.27.237.113:8000/upload/cv_evaluate" \
  -F "file=@/path/to/resume.pdf" \
  -F "jd_text=Optional job description text"
```

## ▶️ Upload CV for Improvements
```bash
curl -X POST "http://34.27.237.113:8000/upload/cv_improvement" \
  -F "file=@/path/to/resume.pdf" \
  -F "jd_text=Optional job description text"
```

---

# 📁 Artifact Uploads (`/uploads`)

## ▶️ Upload CV File
```bash
curl -X POST "http://34.27.237.113:8000/uploads/cv" \
  -F "file=@/path/to/resume.pdf"
```

## ▶️ Upload JD File
```bash
curl -X POST "http://34.27.237.113:8000/uploads/jd" \
  -F "file=@/path/to/jd.pdf"
```

## ▶️ Get Artifact Info
```bash
curl "http://34.27.237.113:8000/uploads/<artifact_id>"
```

## ▶️ Delete Artifact
```bash
curl -X DELETE "http://34.27.237.113:8000/uploads/<artifact_id>"
```

---

# 📦 Session CRUD (`/sessions`)

## ▶️ Create Session (Mock)
```bash
curl -X POST "http://34.27.237.113:8000/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Backend",
    "industry": "Software",
    "company": "Acme",
    "cv_file_id": "cv123",
    "jd_file_id": "jd456"
  }'
```

## ▶️ Get a Session
```bash
curl "http://34.27.237.113:8000/sessions/<session_id>"
```

## ▶️ List Sessions
```bash
curl "http://34.27.237.113:8000/sessions/"
```

## ▶️ Get Next Question
```bash
curl "http://34.27.237.113:8000/sessions/<session_id>/next-question"
```

## ▶️ Submit Answer (Mock)
```bash
curl -X POST "http://34.27.237.113:8000/sessions/<session_id>/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "<id>",
    "text": "My answer",
    "audio_url": ""
  }'
```

## ▶️ Get Session Report
```bash
curl "http://34.27.237.113:8000/sessions/<session_id>/report"
```

## ▶️ Delete Session
```bash
curl -X DELETE "http://34.27.237.113:8000/sessions/<session_id>"
```

---

# 📝 CV vs JD Evaluation (`/evaluation/cv`)
```bash
curl -X POST "http://34.27.237.113:8000/evaluation/cv" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "<resume text>",
    "jd_text": "<job description>"
  }'
```

---

# ⚡ Developer Tips

### PowerShell JSON Quoting
```powershell
$body = @'
{
  "cv_text": "example",
  "jd_text": "example"
}
'@

curl -X POST http://34.27.237.113:8000/v1/cv/fit-index `
  -H "Content-Type: application/json" `
  -d $body
```

### Swagger Docs
Visit the interactive UI:  
```
http://34.27.237.113:8000/docs
```

---

# ✔️ End of File
