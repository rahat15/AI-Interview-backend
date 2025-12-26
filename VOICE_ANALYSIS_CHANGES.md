# Voice Analysis Integration - API Changes Documentation

## Overview
This document outlines all changes made to integrate voice analysis capabilities into the Interview Coach API, enabling voice-only interview evaluation with comprehensive speech analysis.

---

## 🔄 Endpoint Changes

### **Modified Endpoints**

#### `/start` - Start Interview Session
**Enhanced to support Resume and JD IDs:**
```bash
# Using MongoDB document IDs (recommended)
curl -X POST "http://34.27.237.113:8000/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "session_id": "session-123",
    "role_title": "Backend Engineer",
    "company_name": "Acme",
    "industry": "Software",
    "cv_id": "67638f123456789abcdef012",
    "jd_id": "67638f987654321fedcba098",
    "round_type": "full"
  }'
```

**New Fields:**
- ✅ **`cv_id`**: MongoDB ObjectId of uploaded resume
- ✅ **`jd_id`**: MongoDB ObjectId of uploaded job description
- ✅ **Automatic Content Fetching**: System retrieves CV/JD content from database

#### `/answer` - Submit Voice Answer
**BEFORE:**
```bash
# JSON format with text answer
curl -X POST "http://34.27.237.113:8000/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "session_id": "session-123", 
    "answer": "My text answer"
  }'
```

**AFTER:**
```bash
# Form data with required audio file
curl -X POST "http://34.27.237.113:8000/answer" \
  -F "user_id=user-123" \
  -F "session_id=session-123" \
  -F "audio_file=@/path/to/audio.wav"
```

**Changes:**
- ✅ **Input Format**: JSON → Form Data
- ✅ **Required Fields**: `audio_file` (required), removed `answer` text field
- ✅ **Processing**: Automatic speech-to-text conversion
- ✅ **Analysis**: Combined text + voice evaluation

---

## 📊 Response Schema Changes

### **Enhanced Evaluation Response**

#### **BEFORE** (Text-only evaluation):
```json
{
  "evaluation": {
    "score": 3.5,
    "feedback": "Good answer",
    "suggestions": ["Add more details"],
    "breakdown": {
      "relevance": 1.2,
      "depth": 0.8,
      "structure": 0.5,
      "examples": 0.3,
      "technical": 0.4,
      "alignment": 0.3
    },
    "total_possible": 5.0
  }
}
```

#### **AFTER** (Voice + Text evaluation):
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
  }
}
```

**New Fields Added:**
- ✅ **`voice_metrics`**: Detailed speech analysis data
- ✅ **Voice breakdown scores**: `fluency`, `clarity`, `confidence`, `pace`
- ✅ **Enhanced feedback**: Voice-specific suggestions
- ✅ **Updated scoring**: 11-point scale (5 text + 6 voice)

---

## 🗃️ Session State Schema Changes

### **Interview History Enhancement**

#### **BEFORE:**
```json
{
  "history": [
    {
      "question": "Tell me about yourself",
      "answer": "I am a software engineer...",
      "evaluation": {...},
      "stage": "intro",
      "timestamp": "2025-12-26T11:12:29.587461"
    }
  ]
}
```

#### **AFTER:**
```json
{
  "history": [
    {
      "question": "Tell me about yourself",
      "answer": "I am a software engineer...",
      "transcribed_text": "I am a software engineer...",
      "has_audio": true,
      "evaluation": {...},
      "stage": "intro", 
      "timestamp": "2025-12-26T11:12:29.587461"
    }
  ]
}
```

**New Fields:**
- ✅ **`transcribed_text`**: Speech-to-text conversion result
- ✅ **`has_audio`**: Boolean flag indicating voice data presence
- ✅ **`asked_questions`**: Array tracking question variety

---

## 🆕 New Components Added

### **1. Resume/JD Content Fetching**
**Enhanced in:** `apps/api/interview_routes.py`

**Features:**
- MongoDB document retrieval by ObjectId
- HTTP content fetching from file paths
- Fallback to resume stats extraction
- Error handling for missing documents

**Functions:**
- `fetch_resume_content(resume_id)`: Retrieves CV content from MongoDB
- `fetch_jd_content(jd_id)`: Retrieves JD content from MongoDB

### **2. Voice Analyzer Module**
**File:** `interview/voice_analyzer.py`

**Features:**
- Audio processing using `librosa`
- Speech rate estimation (WPM)
- Pitch analysis (mean, variation, range)
- Energy/volume analysis
- Pause pattern detection
- 4-dimensional voice scoring

### **3. Speech-to-Text Converter**
**File:** `interview/speech_to_text.py`

**Features:**
- Google Speech Recognition integration
- Fallback functionality for testing
- Audio format handling
- Error handling and recovery

### **4. Enhanced Session Manager**
**Updates to:** `interview/session_manager.py`

**New Methods:**
- `_evaluate_voice_answer()`: Voice-specific evaluation
- `_combine_text_voice_scores()`: Score integration
- `_evaluate_text_answer()`: Separated text evaluation

---

## 📋 New Dependencies

### **Required Libraries:**
```txt
# Audio processing for voice analysis
librosa==0.10.1
soundfile==0.12.1

# Speech recognition for voice-to-text (optional)
# SpeechRecognition==3.10.0
# pyaudio==0.2.11
```

---

## 🎯 Voice Scoring Breakdown

### **Voice Evaluation Dimensions:**

| Dimension | Max Points | Criteria |
|-----------|------------|----------|
| **Fluency** | 2.0 | Speech rate (140-180 WPM), pause patterns |
| **Clarity** | 1.5 | Volume consistency, energy levels |
| **Confidence** | 1.5 | Pitch variation, energy, pace |
| **Pace** | 1.0 | Speaking speed, duration appropriateness |
| **Total** | 6.0 | Combined voice score |

### **Voice Metrics Tracked:**
- **Duration**: Total speaking time (seconds)
- **Speech Rate**: Estimated words per minute
- **Average Pitch**: Fundamental frequency (Hz)
- **Pitch Variation**: Standard deviation of pitch
- **Average Energy**: RMS energy level
- **Pause Ratio**: Silence to speech ratio
- **Speech Segments**: Number of continuous speech parts

---

## 🔧 Technical Implementation

### **Audio Processing Pipeline:**
1. **Upload** → Audio file received via form data
2. **Conversion** → Speech-to-text using Google API
3. **Analysis** → Parallel text and voice evaluation
4. **Scoring** → Combined 11-point assessment
5. **Feedback** → Voice-specific suggestions

### **Error Handling:**
- Speech recognition failures → Graceful fallback
- Audio processing errors → Default voice scores
- Missing audio → Text-only evaluation mode

---

## 🧪 Testing Commands

### **Complete Voice Interview Flow:**

```bash
# 1. Start Session with Resume and JD IDs
curl -X POST "http://34.27.237.113:8000/start" \
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

# Alternative: Start Session with direct text (fallback)
curl -X POST "http://34.27.237.113:8000/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "session-001", 
    "role_title": "Senior Backend Engineer",
    "company_name": "TechCorp Inc",
    "industry": "Technology",
    "jd": "Senior backend role requiring Python, Node.js",
    "cv": "Experienced Python developer with 5+ years",
    "round_type": "full"
  }'

# 2. Submit Voice Answer
curl -X POST "http://34.27.237.113:8000/answer" \
  -F "user_id=test-user-001" \
  -F "session_id=session-001" \
  -F "audio_file=@test-audio.wav"

# 3. Check Results
curl "http://34.27.237.113:8000/state/test-user-001/session-001"
```

---

## 📈 Benefits

### **Enhanced Interview Experience:**
- ✅ **Realistic Assessment**: Voice + content evaluation
- ✅ **Comprehensive Feedback**: Speech delivery insights
- ✅ **Professional Skills**: Communication assessment
- ✅ **Detailed Analytics**: Voice pattern analysis

### **Technical Advantages:**
- ✅ **Automatic Transcription**: No manual text input
- ✅ **Real-time Processing**: Immediate voice analysis
- ✅ **Scalable Architecture**: Modular voice components
- ✅ **Fallback Support**: Graceful error handling

---

## 🚀 Future Enhancements

### **Potential Improvements:**
- Real-time voice analysis during recording
- Multiple language support for speech recognition
- Advanced voice emotion detection
- Voice similarity matching for consistency
- Integration with video analysis for complete assessment

---

*This documentation covers all changes made to integrate comprehensive voice analysis capabilities into the Interview Coach API system.*