# API Request/Response Examples

## Complete Interview Flow with Video Analysis

### 1. Start Interview Session

**Request:**
```bash
curl -X POST "http://localhost:8000/interview/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "6968966ba463d2d4480cbe48",
    "session_id": "session_123_technical_456",
    "role_title": "Senior Backend Developer",
    "company_name": "TechCorp",
    "industry": "Technology",
    "jd": "We are looking for a senior backend developer with 5+ years experience in Python, FastAPI, and microservices.",
    "cv": "Experienced backend developer with 5 years in Python, FastAPI, Docker, and AWS.",
    "round_type": "technical"
  }'
```

**Response:**
```json
{
  "session_id": "session_123_technical_456",
  "user_id": "6968966ba463d2d4480cbe48",
  "first_question": "Tell me about yourself and what draws you to this role.",
  "state": {
    "user_id": "6968966ba463d2d4480cbe48",
    "session_id": "session_123_technical_456",
    "role_title": "Senior Backend Developer",
    "company_name": "TechCorp",
    "industry": "Technology",
    "status": "active",
    "completed": false,
    "history": [
      {
        "question": "Tell me about yourself and what draws you to this role.",
        "answer": null,
        "evaluation": null,
        "stage": "intro",
        "timestamp": "2026-01-15T10:00:00.000000"
      }
    ]
  },
  "cv_content": "Experienced backend developer with 5 years in Python...",
  "jd_content": "We are looking for a senior backend developer..."
}
```

---

### 2. Submit Video Answer (with Audio)

**Request:**
```bash
curl -X POST "http://localhost:8000/interview/answer" \
  -F "user_id=6968966ba463d2d4480cbe48" \
  -F "session_id=session_123_technical_456" \
  -F "audio_file=@answer_audio.mp3" \
  -F "video_file=@answer_video.mp4"
```

**Response:**
```json
{
  "evaluation": {
    "score": 8.5,
    "feedback": "Strong technical answer with good examples. Demonstrated clear understanding of microservices architecture.",
    "strengths": [
      "Clear communication",
      "Relevant experience",
      "Technical depth"
    ],
    "areas_for_improvement": [
      "Could provide more specific metrics",
      "Elaborate on team collaboration"
    ]
  },
  "technical": {
    "technical_accuracy": 9.0,
    "depth_of_knowledge": 8.5,
    "problem_solving": 8.0,
    "best_practices": 8.5
  },
  "communication": {
    "clarity": 8.5,
    "structure": 8.0,
    "confidence": 9.0,
    "engagement": 8.5
  },
  "video_analysis": {
    "duration_seconds": 45.3,
    "total_frames": 1359,
    "fps": 30.0,
    "face_metrics": {
      "face_presence_percentage": 98.5,
      "multiple_faces_detected_percentage": 0.0,
      "face_detected_frames": 1339
    },
    "eye_contact": {
      "average_score": 0.85,
      "looking_away_percentage": 8.2,
      "rating": "Excellent"
    },
    "blink_analysis": {
      "total_blinks": 18,
      "blinks_per_minute": 23.8,
      "rating": "Normal"
    },
    "head_movement": {
      "stability_score": 0.82,
      "rating": "Stable"
    },
    "cheating_detection": {
      "risk_level": "NONE",
      "risk_score": 5,
      "indicators": [],
      "is_suspicious": false
    },
    "overall_behavior_score": {
      "score": 85.4,
      "rating": "Excellent",
      "confidence": "High"
    }
  },
  "next_question": "Can you describe a challenging technical problem you solved recently?",
  "state": {
    "user_id": "6968966ba463d2d4480cbe48",
    "session_id": "session_123_technical_456",
    "status": "active",
    "completed": false,
    "history": [
      {
        "question": "Tell me about yourself and what draws you to this role.",
        "answer": "I'm a backend developer with 5 years of experience...",
        "evaluation": {
          "score": 8.5,
          "feedback": "Strong technical answer..."
        },
        "stage": "intro",
        "timestamp": "2026-01-15T10:00:00.000000"
      },
      {
        "question": "Can you describe a challenging technical problem you solved recently?",
        "answer": null,
        "evaluation": null,
        "stage": "technical_deep_dive",
        "timestamp": "2026-01-15T10:01:30.000000"
      }
    ]
  }
}
```

---

### 3. Submit Video Answer (Video Only - No Audio)

**Request:**
```bash
curl -X POST "http://localhost:8000/interview/answer" \
  -F "user_id=6968966ba463d2d4480cbe48" \
  -F "session_id=session_123_technical_456" \
  -F "video_file=@answer_video.mp4"
```

**Response:**
```json
{
  "evaluation": null,
  "technical": null,
  "communication": null,
  "video_analysis": {
    "duration_seconds": 30.5,
    "total_frames": 915,
    "fps": 30.0,
    "face_metrics": {
      "face_presence_percentage": 95.2,
      "multiple_faces_detected_percentage": 0.0,
      "face_detected_frames": 871
    },
    "eye_contact": {
      "average_score": 0.78,
      "looking_away_percentage": 15.3,
      "rating": "Good"
    },
    "blink_analysis": {
      "total_blinks": 12,
      "blinks_per_minute": 23.6,
      "rating": "Normal"
    },
    "head_movement": {
      "stability_score": 0.75,
      "rating": "Stable"
    },
    "cheating_detection": {
      "risk_level": "NONE",
      "risk_score": 8,
      "indicators": [],
      "is_suspicious": false
    },
    "overall_behavior_score": {
      "score": 78.5,
      "rating": "Good",
      "confidence": "High"
    }
  },
  "next_question": "What's your experience with cloud platforms like AWS or Azure?",
  "state": {
    "status": "active",
    "completed": false
  }
}
```

---

### 4. Cheating Detected Example

**Request:**
```bash
curl -X POST "http://localhost:8000/interview/answer" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "video_file=@suspicious_video.mp4"
```

**Response:**
```json
{
  "evaluation": null,
  "video_analysis": {
    "duration_seconds": 60.0,
    "total_frames": 1800,
    "fps": 30.0,
    "face_metrics": {
      "face_presence_percentage": 65.5,
      "multiple_faces_detected_percentage": 12.3,
      "face_detected_frames": 1179
    },
    "eye_contact": {
      "average_score": 0.35,
      "looking_away_percentage": 58.7,
      "rating": "Poor"
    },
    "blink_analysis": {
      "total_blinks": 45,
      "blinks_per_minute": 45.0,
      "rating": "High (possible nervousness)"
    },
    "head_movement": {
      "stability_score": 0.32,
      "rating": "Unstable"
    },
    "cheating_detection": {
      "risk_level": "HIGH",
      "risk_score": 67,
      "indicators": [
        "Multiple faces detected frequently",
        "Excessive looking away from camera",
        "Unusual head movement patterns"
      ],
      "is_suspicious": true
    },
    "overall_behavior_score": {
      "score": 28.3,
      "rating": "Poor",
      "confidence": "Medium"
    }
  },
  "next_question": "Can you explain your approach to system design?",
  "state": {
    "status": "active",
    "completed": false
  }
}
```

---

### 5. Analyze Video Only (No Session)

**Request:**
```bash
curl -X POST "http://localhost:8000/v1/audio/analyze" \
  -F "video_file=@test_video.mp4"
```

**Response:**
```json
{
  "video_analysis": {
    "duration_seconds": 15.2,
    "total_frames": 456,
    "fps": 30.0,
    "face_metrics": {
      "face_presence_percentage": 100.0,
      "multiple_faces_detected_percentage": 0.0,
      "face_detected_frames": 456
    },
    "eye_contact": {
      "average_score": 0.92,
      "looking_away_percentage": 2.1,
      "rating": "Excellent"
    },
    "blink_analysis": {
      "total_blinks": 5,
      "blinks_per_minute": 19.7,
      "rating": "Normal"
    },
    "head_movement": {
      "stability_score": 0.88,
      "rating": "Stable"
    },
    "cheating_detection": {
      "risk_level": "NONE",
      "risk_score": 2,
      "indicators": [],
      "is_suspicious": false
    },
    "overall_behavior_score": {
      "score": 89.2,
      "rating": "Excellent",
      "confidence": "High"
    }
  }
}
```

---

### 6. Analyze Audio + Video (No Session)

**Request:**
```bash
curl -X POST "http://localhost:8000/v1/audio/analyze" \
  -F "audio_file=@test_audio.mp3" \
  -F "video_file=@test_video.mp4"
```

**Response:**
```json
{
  "transcribed_text": "I have been working as a backend developer for the past 5 years, primarily focusing on Python and FastAPI. My experience includes building microservices, implementing CI/CD pipelines, and optimizing database performance.",
  "voice_analysis": {
    "pitch": {
      "mean": 145.3,
      "std": 12.5,
      "range": [120.5, 180.2]
    },
    "energy": {
      "mean": 0.65,
      "confidence_level": "High"
    },
    "speaking_rate": {
      "words_per_minute": 145,
      "rating": "Normal"
    },
    "pauses": {
      "count": 8,
      "avg_duration": 0.8,
      "rating": "Natural"
    }
  },
  "video_analysis": {
    "duration_seconds": 45.3,
    "face_metrics": {
      "face_presence_percentage": 98.5,
      "multiple_faces_detected_percentage": 0.0
    },
    "eye_contact": {
      "average_score": 0.85,
      "rating": "Excellent"
    },
    "cheating_detection": {
      "risk_level": "NONE",
      "risk_score": 5,
      "is_suspicious": false
    },
    "overall_behavior_score": {
      "score": 85.4,
      "rating": "Excellent"
    }
  }
}
```

---

## Response Field Explanations

### Video Analysis Fields

| Field | Type | Description |
|-------|------|-------------|
| `duration_seconds` | float | Video duration in seconds |
| `total_frames` | int | Total frames processed |
| `fps` | float | Frames per second |
| `face_presence_percentage` | float | % of frames with face detected |
| `multiple_faces_detected_percentage` | float | % of frames with >1 face |
| `average_score` | float | Eye contact score (0-1) |
| `looking_away_percentage` | float | % of time looking away |
| `total_blinks` | int | Number of blinks detected |
| `blinks_per_minute` | float | Blink rate |
| `stability_score` | float | Head stability (0-1) |
| `risk_level` | string | NONE, LOW, MEDIUM, HIGH |
| `risk_score` | int | Cheating risk score (0-100) |
| `indicators` | array | List of suspicious behaviors |
| `is_suspicious` | boolean | True if risk_score >= 30 |
| `overall_behavior_score.score` | float | Overall score (0-100) |
| `overall_behavior_score.rating` | string | Excellent, Good, Fair, Poor |

### Evaluation Fields

| Field | Type | Description |
|-------|------|-------------|
| `score` | float | Overall answer score (0-10) |
| `feedback` | string | Detailed feedback text |
| `strengths` | array | List of strengths |
| `areas_for_improvement` | array | Areas to improve |
| `technical_accuracy` | float | Technical correctness (0-10) |
| `depth_of_knowledge` | float | Knowledge depth (0-10) |
| `clarity` | float | Communication clarity (0-10) |
| `confidence` | float | Confidence level (0-10) |

---

## Error Responses

### 400 - Bad Request
```json
{
  "detail": {
    "error": "Either audio or video file is required"
  }
}
```

### 404 - Session Not Found
```json
{
  "detail": {
    "error": "Session not found for user_id: user123, session_id: session456"
  }
}
```

### 500 - Processing Error
```json
{
  "detail": "Error processing audio/video: Invalid video format"
}
```

---

## Tips

1. **Video Format**: MP4, AVI, MOV supported
2. **Audio Format**: MP3, WAV, M4A supported
3. **File Size**: Keep videos under 100MB for best performance
4. **Duration**: 30-60 seconds recommended per answer
5. **Quality**: 720p or higher for best face detection
6. **Lighting**: Good lighting improves accuracy
7. **Position**: Face should be centered and visible

---

## Testing Commands

### Quick Test (Video Only)
```bash
curl -X POST "http://localhost:8000/v1/audio/analyze" \
  -F "video_file=@test.mp4"
```

### Full Interview Flow Test
```bash
# 1. Start session
SESSION_ID="test_$(date +%s)"
curl -X POST "http://localhost:8000/interview/start" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"test_user\",\"session_id\":\"$SESSION_ID\",\"role_title\":\"Developer\",\"company_name\":\"TestCo\",\"industry\":\"Tech\",\"jd\":\"Developer role\",\"cv\":\"5 years exp\",\"round_type\":\"technical\"}"

# 2. Submit answer
curl -X POST "http://localhost:8000/interview/answer" \
  -F "user_id=test_user" \
  -F "session_id=$SESSION_ID" \
  -F "video_file=@answer.mp4"
```
