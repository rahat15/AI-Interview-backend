# Interview Voice Analysis Endpoints - API Documentation

## Base URL
```
http://34.27.237.113:8000/api/interview/
```

---

## 🎤 Voice-Enabled Interview Endpoints

### **1. POST `/api/interview/start` - Start Interview Session**

#### **Input (JSON):**
```json
{
  "user_id": "test-user-001",
  "session_id": "session-001",
  "role_title": "Senior Backend Engineer", 
  "company_name": "TechCorp Inc",
  "industry": "Technology",
  "cv_id": "67638f123456789abcdef012",
  "jd_id": "67638f987654321fedcba098",
  "round_type": "full"
}
```

#### **Response:**
```json
{
  "user_id": "test-user-001",
  "session_id": "session-001",
  "first_question": "Tell me about yourself and what draws you to this role.",
  "state": {
    "user_id": "test-user-001",
    "session_id": "session-001",
    "role_title": "Senior Backend Engineer",
    "company_name": "TechCorp Inc",
    "industry": "Technology",
    "status": "active",
    "history": [
      {
        "question": "Tell me about yourself and what draws you to this role.",
        "answer": null,
        "evaluation": null,
        "stage": "intro",
        "timestamp": "2025-12-26T11:12:29.587461"
      }
    ],
    "completed": false
  },
  "cv_content": "Resume: CV (2).pdf\nContact details are clear...",
  "jd_content": "Job Description: Senior backend role requiring Python..."
}
```

#### **Changes Made:**
- ✅ Added `cv_id` and `jd_id` parameters for MongoDB document references
- ✅ Automatic content fetching from database
- ✅ Enhanced response with fetched CV/JD content

---

### **2. POST `/api/interview/answer` - Submit Voice Answer**

#### **Input (Form Data):**
```bash
curl -X POST "http://34.27.237.113:8000/api/interview/answer" \
  -F "user_id=test-user-001" \
  -F "session_id=session-001" \
  -F "audio_file=@/path/to/audio.wav"
```

#### **Response:**
```json
{
  "evaluation": {
    "score": 5.8,
    "feedback": "Good relevance to the question | Good speech fluency | Confident delivery",
    "suggestions": [
      "Add more specific details about your experience",
      "Include concrete examples with measurable results",
      "Speak more clearly and maintain consistent volume"
    ],
    "breakdown": {
      "relevance": 1.3,
      "depth": 0.7,
      "structure": 0.3,
      "examples": 0.2,
      "technical": 0.0,
      "alignment": 0.3,
      "fluency": 1.0,
      "clarity": 0.8,
      "confidence": 0.8,
      "pace": 0.6
    },
    "voice_metrics": {
      "duration": 15.2,
      "speech_rate": 145,
      "avg_pitch": 180.5,
      "pitch_variation": 25.3,
      "avg_energy": 0.025,
      "pause_ratio": 0.12,
      "speech_segments": 3
    },
    "total_possible": 11.0
  },
  "next_question": "I see you have experience with Python. Can you walk me through a challenging project where you used Python and the technical decisions you made?",
  "state": {
    "user_id": "test-user-001",
    "session_id": "session-001",
    "status": "active",
    "history": [
      {
        "question": "Tell me about yourself and what draws you to this role.",
        "answer": "I am a passionate software engineer with five years of experience in backend development using Python and FastAPI.",
        "transcribed_text": "I am a passionate software engineer with five years of experience in backend development using Python and FastAPI.",
        "has_audio": true,
        "evaluation": {...},
        "stage": "intro",
        "timestamp": "2025-12-26T11:12:29.587461"
      },
      {
        "question": "I see you have experience with Python...",
        "answer": null,
        "evaluation": null,
        "stage": "technical_background",
        "timestamp": "2025-12-26T11:13:15.776636"
      }
    ],
    "completed": false
  }
}
```

#### **Changes Made:**
- ✅ **Input Format**: JSON → Form Data with audio file
- ✅ **Required Field**: `audio_file` (replaces text `answer`)
- ✅ **Speech-to-Text**: Automatic transcription
- ✅ **Voice Analysis**: Added voice metrics and scoring
- ✅ **Enhanced Evaluation**: 11-point scale (5 text + 6 voice)
- ✅ **New Response Fields**: `transcribed_text`, `has_audio`, `voice_metrics`

---

### **3. GET `/api/interview/state/{user_id}/{session_id}` - Get Session State**

#### **Response:**
```json
{
  "user_id": "test-user-001",
  "session_id": "session-001",
  "role_title": "Senior Backend Engineer",
  "company_name": "TechCorp Inc",
  "industry": "Technology",
  "jd": "Job Description content...",
  "cv": "Resume content...",
  "round_type": "full",
  "status": "active",
  "history": [
    {
      "question": "Tell me about yourself and what draws you to this role.",
      "answer": "I am a passionate software engineer...",
      "transcribed_text": "I am a passionate software engineer...",
      "has_audio": true,
      "evaluation": {
        "score": 5.8,
        "voice_metrics": {...},
        "breakdown": {...}
      },
      "stage": "intro",
      "timestamp": "2025-12-26T11:12:29.587461"
    }
  ],
  "completed": false,
  "current_stage": "technical_background",
  "question_count": 2,
  "asked_questions": [
    "Tell me about yourself and what draws you to this role.",
    "I see you have experience with Python..."
  ]
}
```

#### **Changes Made:**
- ✅ Added `transcribed_text` in history items
- ✅ Added `has_audio` flag in history items
- ✅ Added `asked_questions` array for question tracking
- ✅ Enhanced evaluation data with voice metrics

---

### **4. GET `/api/interview/sessions/{user_id}` - Get User Sessions**

#### **Response:**
```json
[
  {
    "session_id": "session-001",
    "role_title": "Senior Backend Engineer",
    "company_name": "TechCorp Inc",
    "status": "active",
    "question_count": 3
  },
  {
    "session_id": "session-002", 
    "role_title": "Frontend Developer",
    "company_name": "StartupCorp",
    "status": "completed",
    "question_count": 8
  }
]
```

#### **Changes Made:**
- ✅ No structural changes to this endpoint
- ✅ Sessions now track voice-enabled interviews

---

### **5. GET `/api/interview/report/{user_id}/{session_id}` - Get Interview Report**

#### **Response:**
```json
{
  "session_id": "session-001",
  "user_id": "test-user-001",
  "role": "Senior Backend Engineer",
  "company": "TechCorp Inc",
  "industry": "Technology",
  "avg_scores": {
    "overall": 6.2,
    "technical": 5.8,
    "communication": 6.5,
    "problem_solving": 6.0,
    "cultural_fit": 6.1
  },
  "history": [
    {
      "question": "Tell me about yourself and what draws you to this role.",
      "answer": "I am a passionate software engineer...",
      "transcribed_text": "I am a passionate software engineer...",
      "has_audio": true,
      "evaluation": {
        "score": 5.8,
        "voice_metrics": {
          "duration": 15.2,
          "speech_rate": 145,
          "avg_pitch": 180.5,
          "fluency": 1.0,
          "clarity": 0.8,
          "confidence": 0.8,
          "pace": 0.6
        },
        "breakdown": {...}
      },
      "stage": "intro"
    }
  ],
  "total_questions": 8,
  "completed": true
}
```

#### **Changes Made:**
- ✅ Enhanced scoring includes voice analysis
- ✅ History items include voice transcription and metrics
- ✅ Overall scores reflect combined text + voice evaluation

---

## 🎯 Voice Analysis Features

### **Voice Metrics Tracked:**
- **Duration**: Total speaking time (seconds)
- **Speech Rate**: Words per minute estimation
- **Average Pitch**: Fundamental frequency (Hz)
- **Pitch Variation**: Voice modulation range
- **Average Energy**: Volume/intensity levels
- **Pause Ratio**: Silence to speech ratio
- **Speech Segments**: Continuous speech parts

### **Voice Scoring (6 points total):**
- **Fluency** (0-2): Speech rate, pause patterns
- **Clarity** (0-1.5): Volume consistency, energy
- **Confidence** (0-1.5): Pitch variation, energy
- **Pace** (0-1): Speaking speed, duration

### **Combined Evaluation:**
- **Text Analysis** (5 points): Content quality
- **Voice Analysis** (6 points): Delivery quality
- **Total Score** (11 points): Scaled to 10-point system

---

## 🧪 Complete Testing Flow

```bash
# 1. Start voice interview
curl -X POST "http://34.27.237.113:8000/api/interview/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "session-001",
    "role_title": "Senior Backend Engineer",
    "company_name": "TechCorp Inc", 
    "industry": "Technology",
    "cv_id": "67638f123456789abcdef012",
    "jd_id": "67638f987654321fedcba098",
    "round_type": "full"
  }'

# 2. Submit voice answers
curl -X POST "http://34.27.237.113:8000/api/interview/answer" \
  -F "user_id=test-user-001" \
  -F "session_id=session-001" \
  -F "audio_file=@answer1.wav"

# 3. Continue interview
curl -X POST "http://34.27.237.113:8000/api/interview/answer" \
  -F "user_id=test-user-001" \
  -F "session_id=session-001" \
  -F "audio_file=@answer2.wav"

# 4. Check session state
curl "http://34.27.237.113:8000/api/interview/state/test-user-001/session-001"

# 5. Get final report
curl "http://34.27.237.113:8000/api/interview/report/test-user-001/session-001"
```

---

*All endpoints under `/api/interview/` prefix now support comprehensive voice analysis with speech-to-text conversion and detailed voice metrics evaluation.*