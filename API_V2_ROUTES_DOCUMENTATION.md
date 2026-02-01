# Interview API V2 - Complete Routes Documentation

## 📋 Table of Contents

- [Overview](#overview)
- [API Endpoints](#api-endpoints)
- [Route Details](#route-details)
- [Request/Response Schemas](#requestresponse-schemas)
- [Changes from V1](#changes-from-v1)
- [Examples](#examples)

---

## Overview

**Base Path:** `/interview/v2/`

**New Features:**
- ✅ MongoDB caching for faster responses
- ✅ Streaming support via Server-Sent Events
- ✅ Performance metrics and monitoring
- ✅ Async/concurrent operations
- ✅ 60-70% faster response times

**Authentication:** None (add as needed)

**Content-Type:** 
- `application/json` for JSON endpoints
- `multipart/form-data` for file uploads
- `text/event-stream` for streaming endpoints

---

## API Endpoints

### Quick Reference Table

| Endpoint | Method | Purpose | Streaming |
|----------|--------|---------|-----------|
| [`/interview/v2/start`](#1-post-interviewv2start) | POST | Start session (direct text) | No |
| [`/interview/v2/start-with-ids`](#2-post-interviewv2start-with-ids) | POST | Start session (MongoDB IDs) | No |
| [`/interview/v2/answer`](#3-post-interviewv2answer) | POST | Submit answer with audio/video | No |
| [`/interview/v2/stream/{session_id}`](#4-get-interviewv2streamsession_id) | GET | Stream question generation | Yes (SSE) |
| [`/interview/v2/state/{session_id}`](#5-get-interviewv2statesession_id) | GET | Get session state | No |
| [`/interview/v2/performance/{session_id}`](#6-get-interviewv2performancesession_id) | GET | Get session metrics | No |
| [`/interview/v2/complete/{session_id}`](#7-post-interviewv2completesession_id) | POST | Complete & evaluate | No |
| [`/interview/v2/metrics/global`](#8-get-interviewv2metricsglobal) | GET | Global performance metrics | No |
| [`/interview/v2/metrics/reset`](#9-post-interviewv2metricsreset) | POST | Reset metrics (admin) | No |

---

## Route Details

### 1. POST `/interview/v2/start`

**Purpose:** Start a new interview session with direct CV/JD text

**Headers Required:**
```
Content-Type: application/json
```

**Request Body (JSON):**
```json
{
  "user_id": "user_123",
  "session_id": "sess_abc",
  "role": "Senior Software Engineer",
  "company": "TechCorp",
  "cv_text": "John Doe\n5 years of experience in Python development...",
  "jd_text": "We are seeking a Senior Software Engineer with expertise in Python..."
}
```

**All fields are required (string type):**
- `user_id`: Unique user identifier
- `session_id`: Unique session identifier  
- `role`: Job role/position title
- `company`: Company name
- `cv_text`: Complete CV/resume content as text
- `jd_text`: Complete job description as text

**Response (200 OK - New Session):**
```json
{
  "session_id": "sess_123",
  "status": "active",
  "question": "Hello! I'm excited to speak with you about the Senior Software Engineer role. To start, could you walk me through your experience with Python and FastAPI?",
  "question_number": 1
}
```

**Response Fields:**
- `session_id` (string): Unique identifier for this interview session
- `status` (string): Session status - "active", "completed", or "restored"
- `question` (string): The first interview question generated based on CV/JD analysis
- `question_number` (integer): Current question number (starts at 1)

**Response (200 OK - Cached/Restored Session):**
```json
{
  "session_id": "sess_123",
  "status": "restored",
  "question": "Tell me about your experience with microservices architecture."
}
```

**Note:** When a session is restored from cache, it returns the last question that was asked.

**Error Response (500 - Server Error):**
```json
{
  "detail": "Failed to analyze CV: Invalid text format"
}
```

**Error Response (400 - Bad Request - Missing Fields):**
```json
{
  "detail": "Missing required field: cv_text"
}
```

**Error Response (400 - Validation Error):**
```json
{
  "detail": [
    {
      "loc": ["body", "user_id"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "cv_text"],
      "msg": "str type expected",
      "type": "type_error.str"
    }
  ]
}
```

**Common Error:** "user_id must be a string, session_id must be a string..."
- **Cause:** Missing `Content-Type: application/json` header or sending form-data instead of JSON
- **Fix:** Ensure you're sending JSON with proper header (see cURL example below)

**Performance:**
- First time (uncached): ~4-6 seconds
- With cached CV: ~2-3 seconds
- Restored session: ~0.5-1 second

---

### 2. POST `/interview/v2/start-with-ids`

**Purpose:** Start session using CV/JD MongoDB IDs, files, or direct text

**Request (Form Data):**
```
user_id: string (required)
session_id: string (required)
role: string (required)
company: string (required)
cv_id: string (optional)
jd_id: string (optional)
cv_file: file (optional, .pdf/.docx/.txt)
jd_file: file (optional, .pdf/.docx/.txt)
cv_text: string (optional)
jd_text: string (optional)
```

**Note:** Provide CV/JD in one of these ways (priority order):
1. **Files** (`cv_file`, `jd_file`) - Recommended, automatic text extraction
2. **MongoDB IDs** (`cv_id`, `jd_id`) - Good for caching
3. **Direct text** (`cv_text`, `jd_text`) - Fallback option

**Response (200 OK - New Session):**
```json
{
  "session_id": "sess_456",
  "status": "active",
  "question": "Thanks for joining us today. I'd like to start by understanding your background. Can you tell me about your experience with the technologies mentioned in the job description?",
  "question_number": 1
}
```

**Response Fields:**
- `session_id` (string): Unique session identifier (echoes your request)
- `status` (string): "active" for new sessions, "restored" for cached sessions
- `question` (string): Context-aware first question based on CV and JD analysis
- `question_number` (integer): Always 1 for new sessions

**Response (200 OK - From File Upload):**
```json
{
  "session_id": "sess_789",
  "status": "active",
  "question": "Hi there! I see you have extensive experience with microservices. Let's start by discussing your background - can you walk me through your most recent project involving distributed systems?",
  "question_number": 1
}
```

**Note:** File uploads are automatically processed:
- PDF: Text extracted using pypdf
- DOCX: Text extracted using python-docx
- TXT: Direct UTF-8 decoding

**Error Response (404 - CV/JD Not Found):**
```json
{
  "detail": "Resume 60d5ec49f1b2c8b1f8c4e5a1 not found"
}
```

**Error Response (400 - Missing Data):**
```json
{
  "detail": "Both CV and JD content required"
}
```

**Error Response (400 - File Format Error):**
```json
{
  "detail": "Unsupported CV file format: .exe"
}
```

**Error Response (400 - File Extraction Failed):**
```json
{
  "detail": "Failed to extract text from PDF: Encrypted file"
}
```

**Performance:**
- With file upload: ~3-5 seconds (includes text extraction)
- With cached CV (by ID): ~2-3 seconds
- Without cache: ~4-6 seconds
- Restored session: ~0.5-1 second

---

### 3. POST `/interview/v2/answer`

**Purpose:** Submit candidate answer with optional audio/video files

**Request (Form Data):**
```
session_id: string (required)
audio_file: file (optional, .wav/.mp3)
video_file: file (optional, .mp4/.webm)
```

**Note:** At least one file (audio or video) is required. If video is provided without audio, audio will be extracted from video.

**Response (200 OK - Active Interview):**
```json
{
  "session_id": "sess_456",
  "status": "active",
  "question": "That's impressive experience. Can you describe a challenging technical problem you solved recently?",
  "question_number": 2,
  "evaluation": {
    "clarity": 8,
    "relevance": 9,
    "depth": 7,
    "feedback": "Clear and relevant answer with good technical details"
  }
}
```

**Response Fields:**
- `session_id` (string): Session identifier
- `status` (string): "active" if interview continues, "completed" if finished
- `question` (string): Next interview question (only if status is "active")
- `question_number` (integer): Current question count
- `evaluation` (object): Evaluation of the previous answer
  - `clarity` (integer, 1-10): How clearly the candidate expressed their answer
  - `relevance` (integer, 1-10): How relevant the answer was to the question
  - `depth` (integer, 1-10): Technical or behavioral depth of the answer
  - `feedback` (string): Brief qualitative feedback on the answer

**Response (200 OK - With Voice Metrics):**
```json
{
  "session_id": "sess_456",
  "status": "active",
  "question": "Great insights! Now, could you explain how you would approach building a rate limiting system?",
  "question_number": 3,
  "evaluation": {
    "clarity": 9,
    "relevance": 8,
    "depth": 8,
    "feedback": "Excellent explanation with specific examples and metrics"
  },
  "voice_analysis": {
    "fluency_score": 8.5,
    "clarity_score": 9.0,
    "confidence_score": 7.8,
    "pace_score": 8.2,
    "rate_wpm": 145,
    "total_score": 8.4
  }
}
```

**Note:** Voice analysis is included when audio is successfully processed.

**Response (200 OK - Interview Complete):**
```json
{
  "session_id": "sess_456",
  "status": "completed",
  "message": "Interview completed",
  "total_questions": 5
}
```

**Response Fields (Completed):**
- `session_id` (string): Session identifier
- `status` (string): "completed"
- `message` (string): Completion message
- `total_questions` (integer): Total number of questions asked in the interview

**Note:** When interview is completed, call `/interview/v2/complete/{session_id}` to get full evaluation.

**Error Response (404 - Session Not Found):**
```json
{
  "detail": "Session not found"
}
```

**Error Response (400 - No Files):**
```json
{
  "detail": {
    "error": "Either audio or video file is required"
  }
}
```

**Performance:**
- Answer processing: ~2-4 seconds
- Includes transcription + evaluation + next question

**Features:**
- Automatic audio transcription (Gemini)
- Voice analysis (if available)
- Video analysis (if provided)
- Concurrent processing

---

### 4. GET `/interview/v2/stream/{session_id}`

**Purpose:** Stream next question generation in real-time (Server-Sent Events)

**Parameters:**
- `session_id` (path): Session identifier

**Response (200 OK - Event Stream):**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"chunk": "Tell me about"}

data: {"chunk": " your experience"}

data: {"chunk": " with Python..."}

data: {"done": true}
```

**Error Response (Event Stream):**
```
data: {"error": "Session not found"}
```

**Client Example (JavaScript):**
```javascript
const eventSource = new EventSource('/interview/v2/stream/sess_456');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.chunk) {
    // Display chunk in real-time
    document.getElementById('question').innerText += data.chunk;
  }
  
  if (data.done) {
    eventSource.close();
  }
  
  if (data.error) {
    console.error(data.error);
    eventSource.close();
  }
};
```

**Performance:**
- First chunk: ~0.5-1 second
- Complete question: ~2-3 seconds
- Progressive display for better UX

---

### 5. GET `/interview/v2/state/{session_id}`

**Purpose:** Get current session state and conversation history

**Parameters:**
- `session_id` (path): Session identifier

**Response (200 OK - Complete Session State):**
```json
{
  "session_id": "sess_456",
  "user_id": "user_123",
  "role": "Senior Software Engineer",
  "company": "TechCorp",
  "question_count": 3,
  "stage": "technical",
  "completed": false,
  "messages": [
    {
      "role": "interviewer",
      "content": "Tell me about your experience with Python and backend development.",
      "timestamp": 1706745600.123,
      "metadata": {
        "stage": "intro"
      }
    },
    {
      "role": "candidate",
      "content": "I have 5 years of experience working with Python, primarily in backend development using FastAPI and Django. I've built several microservices that handle millions of requests daily.",
      "timestamp": 1706745620.456,
      "metadata": {
        "evaluation": {
          "clarity": 8,
          "relevance": 9,
          "depth": 7,
          "feedback": "Good answer with specific technologies and scale mentioned"
        },
        "voice_metrics": {
          "fluency_score": 8.5,
          "clarity_score": 8.0,
          "confidence_score": 7.5
        }
      }
    },
    {
      "role": "interviewer",
      "content": "That's impressive. Can you describe your experience with microservices architecture?",
      "timestamp": 1706745640.789,
      "metadata": {
        "stage": "technical"
      }
    },
    {
      "role": "candidate",
      "content": "I've designed and implemented a microservices architecture using Docker and Kubernetes. We split our monolith into 12 services, each with its own database...",
      "timestamp": 1706745670.234,
      "metadata": {
        "evaluation": {
          "clarity": 9,
          "relevance": 9,
          "depth": 8,
          "feedback": "Excellent technical depth with concrete implementation details"
        }
      }
    },
    {
      "role": "interviewer",
      "content": "Excellent. Now, could you walk me through a challenging technical problem you recently solved?",
      "timestamp": 1706745690.567,
      "metadata": {
        "stage": "technical"
      }
    }
  ],
  "avg_response_time": 2.34
}
```

**Response Fields:**
- `session_id` (string): Unique session identifier
- `user_id` (string): User identifier
- `role` (string): Job role being interviewed for
- `company` (string): Company name
- `question_count` (integer): Total questions asked so far
- `stage` (string): Current interview stage ("intro", "technical", "behavioral", "closing")
- `completed` (boolean): Whether interview is finished
- `messages` (array): Complete conversation history
  - Each message contains:
    - `role`: "interviewer" or "candidate"
    - `content`: Message text
    - `timestamp`: Unix timestamp
    - `metadata`: Additional data (stage, evaluation, voice metrics)
- `avg_response_time` (float): Average time to generate questions (seconds)

**Error Response (404 - Not Found):**
```json
{
  "detail": "Session not found"
}
```

**Error Response (500 - Server Error):**
```json
{
  "detail": "Failed to retrieve session state: Database connection error"
}
```

**Use Cases:**
- Resume interrupted session
- Review conversation history
- Check session progress
- Debug issues

---

### 6. GET `/interview/v2/performance/{session_id}`

**Purpose:** Get performance metrics for a specific session

**Parameters:**
- `session_id` (path): Session identifier

**Response (200 OK - Detailed Performance Metrics):**
```json
{
  "session_id": "sess_456",
  "total_questions": 5,
  "response_times": {
    "min": 1.23,
    "max": 4.56,
    "avg": 2.45,
    "all": [4.56, 2.12, 2.34, 1.98, 1.23]
  },
  "cache_status": "active"
}
```

**Response Fields:**
- `session_id` (string): Session identifier
- `total_questions` (integer): Total questions generated in this session
- `response_times` (object): Performance timing data
  - `min` (float): Fastest question generation time (seconds)
  - `max` (float): Slowest question generation time (seconds)
  - `avg` (float): Average generation time (seconds)
  - `all` (array): All response times in chronological order
- `cache_status` (string): "active" if CV/JD are cached, "not_cached" otherwise

**Performance Interpretation:**
- **min < 2s**: Excellent performance, likely using cached context
- **avg < 3s**: Good performance, meeting target SLAs
- **max > 5s**: Some slow operations, check logs for bottlenecks
- **cache_status = "active"**: CV analysis is cached, subsequent sessions will be faster

**Error Response (404 - Not Found):**
```json
{
  "detail": "Session not found"
}
```

**Error Response (500 - Server Error):**
```json
{
  "detail": "Failed to retrieve performance metrics: Internal error"
}
```

**Metrics Explained:**
- `min`: Fastest question generation time
- `max`: Slowest question generation time
- `avg`: Average response time
- `all`: All response times in order
- `cache_status`: Whether CV/JD are cached

**Use Cases:**
- Monitor session performance
- Identify slow operations
- Validate caching effectiveness
- Performance debugging

---

### 7. POST `/interview/v2/complete/{session_id}`

**Purpose:** Complete interview and generate comprehensive evaluation

**Parameters:**
- `session_id` (path): Session identifier

**Response (200 OK - Complete Interview Evaluation):**
```json
{
  "session_id": "sess_456",
  "status": "completed",
  "total_questions": 5,
  "evaluation": {
    "overall_score": 7.83,
    "recommendation": "hire",
    "clarity": 8.2,
    "relevance": 8.4,
    "depth": 6.9
  },
  "conversation": [
    {
      "question": "Tell me about your experience with Python and backend development.",
      "answer": "I have 5 years of experience working with Python, primarily in backend development using FastAPI and Django. I've built several microservices that handle millions of requests daily.",
      "evaluation": {
        "clarity": 8,
        "relevance": 9,
        "depth": 7,
        "feedback": "Good answer with specific technologies and scale mentioned"
      }
    },
    {
      "question": "Can you describe your experience with microservices architecture?",
      "answer": "I've designed and implemented a microservices architecture using Docker and Kubernetes. We split our monolith into 12 services, each with its own database. We used RabbitMQ for async communication and implemented circuit breakers for resilience.",
      "evaluation": {
        "clarity": 9,
        "relevance": 9,
        "depth": 8,
        "feedback": "Excellent technical depth with concrete implementation details"
      }
    },
    {
      "question": "Describe a challenging technical problem you recently solved.",
      "answer": "I once optimized our database queries which were causing timeouts. I implemented query caching, added proper indexes, and restructured some N+1 queries. This reduced average response time from 3 seconds to 200ms.",
      "evaluation": {
        "clarity": 9,
        "relevance": 8,
        "depth": 8,
        "feedback": "Excellent technical depth with measurable results"
      }
    },
    {
      "question": "Tell me about a time when you had to work with a difficult team member.",
      "answer": "I worked with a senior engineer who was resistant to code reviews. I scheduled a one-on-one to understand their perspective, and we agreed on a lighter review process focusing on critical issues.",
      "evaluation": {
        "clarity": 8,
        "relevance": 8,
        "depth": 6,
        "feedback": "Good behavioral answer showing conflict resolution"
      }
    },
    {
      "question": "Do you have any questions for me about the role or company?",
      "answer": "Yes, I'm curious about the team structure and what technologies you're using for your microservices deployment.",
      "evaluation": {
        "clarity": 7,
        "relevance": 8,
        "depth": 6,
        "feedback": "Relevant questions showing interest in technical details"
      }
    }
  ],
  "performance_metrics": {
    "avg_response_time": 2.45,
    "total_response_times": [4.56, 2.12, 2.34, 1.98, 1.23]
  }
}
```

**Response Fields:**
- `session_id` (string): Session identifier
- `status` (string): "completed"
- `total_questions` (integer): Total questions asked
- `evaluation` (object): Overall evaluation metrics
  - `overall_score` (float): Average of clarity, relevance, depth (1-10)
  - `recommendation` (string): "hire", "maybe", or "no_hire"
  - `clarity` (float): Average clarity score across all answers
  - `relevance` (float): Average relevance score
  - `depth` (float): Average depth score
- `conversation` (array): Complete Q&A history with evaluations
  - Each entry contains:
    - `question` (string): The question asked
    - `answer` (string): Candidate's response
    - `evaluation` (object): Individual answer evaluation
- `performance_metrics` (object): System performance data
  - `avg_response_time` (float): Average question generation time
  - `total_response_times` (array): All response times

**Recommendation Criteria:**
- **hire**: overall_score >= 8.0 (Strong candidate)
- **maybe**: overall_score >= 6.0 and < 8.0 (Moderate candidate)
- **no_hire**: overall_score < 6.0 (Weak candidate)

**Error Response (404 - Not Found):**
```json
{
  "detail": "Session not found"
}
```

**Error Response (400 - Bad Request):**
```json
{
  "detail": "Session is not completed yet. Current status: active"
}
```

**Error Response (500 - Server Error):**
```json
{
  "detail": "Failed to generate evaluation: LLM API error"
}
```

**Evaluation Criteria:**
- **overall_score**: Average of clarity, relevance, depth (1-10)
- **recommendation**: 
  - `hire` (score >= 8)
  - `maybe` (score >= 6)
  - `no_hire` (score < 6)
- **clarity**: How clear the answers were
- **relevance**: How relevant to the questions
- **depth**: Technical/behavioral depth

---

### 8. GET `/interview/v2/metrics/global`

**Purpose:** Get global performance metrics across all sessions

**Response (200 OK - Complete Global Metrics):**
```json
{
  "status": "success",
  "metrics": {
    "llm_calls": {
      "total": 127,
      "avg_duration": 2.34,
      "min_duration": 0.89,
      "max_duration": 5.67
    },
    "api_requests": {
      "total": 89,
      "avg_duration": 3.12,
      "min_duration": 1.23,
      "max_duration": 8.45
    },
    "cache": {
      "hits": 54,
      "misses": 35,
      "hit_rate": 0.6067,
      "hit_rate_percentage": "60.7%"
    }
  },
  "timestamp": 1706745600.123
}
```

**Response Fields:**
- `status` (string): "success" if metrics retrieved successfully
- `metrics` (object): Performance metrics across all sessions
  - `llm_calls` (object): Gemini API call statistics
    - `total` (integer): Total number of LLM API calls made
    - `avg_duration` (float): Average call duration in seconds
    - `min_duration` (float): Fastest call duration
    - `max_duration` (float): Slowest call duration
  - `api_requests` (object): API endpoint statistics
    - `total` (integer): Total API requests received
    - `avg_duration` (float): Average request processing time
    - `min_duration` (float): Fastest request
    - `max_duration` (float): Slowest request
  - `cache` (object): Caching effectiveness metrics
    - `hits` (integer): Number of successful cache retrievals
    - `misses` (integer): Number of cache misses
    - `hit_rate` (float): Cache hit rate (0.0 to 1.0)
    - `hit_rate_percentage` (string): Formatted hit rate percentage
- `timestamp` (float): Unix timestamp when metrics were retrieved

**Performance Health Indicators:**

**LLM Calls:**
- ✅ **Healthy**: avg_duration < 2.5s, max_duration < 5s
- ⚠️ **Warning**: avg_duration 2.5-4s, max_duration 5-8s
- ❌ **Critical**: avg_duration > 4s, max_duration > 8s

**API Requests:**
- ✅ **Healthy**: avg_duration < 3s
- ⚠️ **Warning**: avg_duration 3-5s
- ❌ **Critical**: avg_duration > 5s

**Cache Performance:**
- ✅ **Excellent**: hit_rate > 0.7 (70%)
- ✅ **Good**: hit_rate 0.5-0.7 (50-70%)
- ⚠️ **Poor**: hit_rate 0.3-0.5 (30-50%)
- ❌ **Critical**: hit_rate < 0.3 (30%)

**Error Response (500 - Server Error):**
```json
{
  "detail": "Failed to retrieve metrics: Database connection error"
}
```

**Error Response (503 - Service Unavailable):**
```json
{
  "detail": "Metrics service temporarily unavailable"
}
```

**Metrics Breakdown:**

**LLM Calls:**
- All Gemini API calls (question generation, evaluation, analysis)
- Tracks duration to identify slow calls
- Alerts logged for calls > 5s

**API Requests:**
- All endpoint requests
- Measures end-to-end latency
- Alerts for requests > 3s

**Cache Performance:**
- Hit rate indicates caching effectiveness
- Target: > 60% hit rate
- Low hit rate suggests optimization needed

**Use Cases:**
- System health monitoring
- Performance optimization
- Cost analysis
- Capacity planning

---

### 9. POST `/interview/v2/metrics/reset`

**Purpose:** Reset all performance metrics (admin/testing only)

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Metrics reset successfully"
}
```

**Error Response (500):**
```json
{
  "detail": "Error message"
}
```

**Warning:** This clears all performance data. Use only for:
- Testing
- Development
- After analyzing metrics
- Starting fresh monitoring

---

## Request/Response Schemas

### Complete Schema Definitions

#### OptimizedStartRequest
```typescript
{
  user_id: string;        // Unique user identifier
  session_id: string;     // Unique session identifier
  role: string;           // Job role title
  company: string;        // Company name
  cv_text: string;        // Full CV/resume text
  jd_text: string;        // Full job description text
}
```

#### StartWithIdsRequest (Form Data)
```typescript
{
  user_id: string;              // Required
  session_id: string;           // Required
  role: string;                 // Required
  company: string;              // Required
  cv_id?: string;               // MongoDB ObjectId or string ID
  jd_id?: string;               // MongoDB ObjectId or string ID
  cv_file?: File;               // CV file (.pdf, .docx, .txt) - Recommended
  jd_file?: File;               // JD file (.pdf, .docx, .txt) - Recommended
  cv_text?: string;             // Alternative: direct text
  jd_text?: string;             // Alternative: direct text
}
```

#### AnswerRequest (Form Data)
```typescript
{
  session_id: string;           // Required
  audio_file?: File;            // .wav, .mp3, .m4a
  video_file?: File;            // .mp4, .webm, .avi
}
```

#### SessionStateResponse
```typescript
{
  session_id: string;
  user_id: string;
  role: string;
  company: string;
  question_count: number;
  stage: "intro" | "technical" | "behavioral" | "closing";
  completed: boolean;
  messages: Array<{
    role: "interviewer" | "candidate";
    content: string;
    timestamp: number;
    metadata?: {
      stage?: string;
      evaluation?: Evaluation;
      voice_metrics?: VoiceMetrics;
    };
  }>;
  avg_response_time: number;
}
```

#### Evaluation
```typescript
{
  clarity: number;        // 1-10
  relevance: number;      // 1-10
  depth: number;          // 1-10
  feedback: string;       // Brief feedback
}
```

#### PerformanceMetrics
```typescript
{
  session_id: string;
  total_questions: number;
  response_times: {
    min: number;
    max: number;
    avg: number;
    all: number[];
  };
  cache_status: "active" | "not_cached";
}
```

#### GlobalMetrics
```typescript
{
  status: "success";
  metrics: {
    llm_calls: {
      total: number;
      avg_duration: number;
      min_duration: number;
      max_duration: number;
    };
    api_requests: {
      total: number;
      avg_duration: number;
      min_duration: number;
      max_duration: number;
    };
    cache: {
      hits: number;
      misses: number;
      hit_rate: number;
      hit_rate_percentage: string;
    };
  };
  timestamp: number;
}
```

---

## Changes from V1

### Endpoint Mapping

| V1 Endpoint | V2 Endpoint | Changes |
|-------------|-------------|---------|
| `POST /v1/interview/start` | `POST /interview/v2/start-with-ids` | ✅ Added MongoDB ID support<br>✅ Added caching<br>✅ 60% faster |
| `POST /v1/interview/answer` | `POST /interview/v2/answer` | ✅ Added voice analysis<br>✅ Added video support<br>✅ Concurrent processing<br>✅ 50% faster |
| `GET /v1/interview/state/{id}` | `GET /interview/v2/state/{id}` | ✅ Enhanced response<br>✅ Added performance data |
| N/A | `GET /interview/v2/stream/{id}` | ✅ **NEW**: SSE streaming |
| N/A | `GET /interview/v2/performance/{id}` | ✅ **NEW**: Performance metrics |
| N/A | `GET /interview/v2/metrics/global` | ✅ **NEW**: Global analytics |

### Response Changes

#### Start Session Response

**V1:**
```json
{
  "session_id": "sess_123",
  "user_id": "user_123",
  "first_question": "Tell me about yourself.",
  "state": { ... }
}
```

**V2:**
```json
{
  "session_id": "sess_123",
  "status": "active",
  "question": "Tell me about yourself.",
  "question_number": 1
}
```

**Changes:**
- ✅ Simplified response
- ✅ Added `status` field
- ✅ Added `question_number`
- ✅ Removed redundant `state` object
- ✅ 60-70% faster

#### Answer Response

**V1:**
```json
{
  "evaluation": { ... },
  "next_question": "...",
  "state": { ... }
}
```

**V2:**
```json
{
  "session_id": "sess_456",
  "status": "active",
  "question": "...",
  "question_number": 2,
  "evaluation": {
    "clarity": 8,
    "relevance": 9,
    "depth": 7,
    "feedback": "Good answer"
  }
}
```

**Changes:**
- ✅ Added `session_id` for clarity
- ✅ Added `status` for completion tracking
- ✅ Added `question_number`
- ✅ Simplified evaluation structure
- ✅ Removed large `state` object
- ✅ 50-60% faster

### New Features in V2

1. **MongoDB Caching**
   - CV analysis cached for 7 days
   - Session state cached for 24 hours
   - Automatic cache invalidation

2. **Streaming Support**
   - Server-Sent Events for real-time questions
   - Progressive display
   - Better UX

3. **Performance Monitoring**
   - Per-session metrics
   - Global analytics
   - Cache hit rate tracking
   - Slow operation alerts

4. **Async Operations**
   - Parallel CV + JD analysis
   - Non-blocking LLM calls
   - Concurrent processing

5. **Enhanced Error Handling**
   - Better error messages
   - Detailed validation
   - Graceful degradation

---

## Examples

### Example 1: Complete Interview Flow

```bash
# Option A: Start Interview with JSON (v2/start)
curl -X POST http://localhost:8000/interview/v2/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "session_id": "sess_456",
    "role": "Senior Software Engineer",
    "company": "TechCorp",
    "cv_text": "John Doe\\nSenior Software Engineer with 5 years of Python experience...",
    "jd_text": "We are seeking a Senior Software Engineer with expertise in Python, FastAPI, and microservices..."
  }'

# Response:
{
  "session_id": "sess_456",
  "status": "active",
  "question": "Hi! Thanks for joining. Tell me about your Python experience.",
  "question_number": 1
}

# Option B: Start Interview (with file uploads - recommended)
curl -X POST http://localhost:8000/interview/v2/start-with-ids \
  -F "user_id=user_123" \
  -F "session_id=sess_456" \
  -F "role=Senior Software Engineer" \
  -F "company=TechCorp" \
  -F "cv_file=@resume.pdf" \
  -F "jd_file=@job_description.pdf"

# Alternative: Using MongoDB IDs
curl -X POST http://localhost:8000/interview/v2/start-with-ids \
  -F "user_id=user_123" \
  -F "session_id=sess_456" \
  -F "role=Senior Software Engineer" \
  -F "company=TechCorp" \
  -F "cv_id=60d5ec49f1b2c8b1f8c4e5a1" \
  -F "jd_id=60d5ec49f1b2c8b1f8c4e5a2"

# Response:
{
  "session_id": "sess_456",
  "status": "active",
  "question": "Hi! Thanks for joining. Tell me about your Python experience.",
  "question_number": 1
}

# 2. Submit Answer (Audio)
curl -X POST http://localhost:8000/interview/v2/answer \
  -F "session_id=sess_456" \
  -F "audio_file=@answer1.wav"

# Response:
{
  "session_id": "sess_456",
  "status": "active",
  "question": "That's great. Can you describe a challenging project?",
  "question_number": 2,
  "evaluation": {
    "clarity": 8,
    "relevance": 9,
    "depth": 7,
    "feedback": "Clear answer with good details"
  }
}

# 3. Check Performance
curl http://localhost:8000/interview/v2/performance/sess_456

# Response:
{
  "session_id": "sess_456",
  "total_questions": 2,
  "response_times": {
    "min": 2.12,
    "max": 4.56,
    "avg": 3.34,
    "all": [4.56, 2.12]
  },
  "cache_status": "active"
}

# 4. Complete Interview (after 5 questions)
curl -X POST http://localhost:8000/interview/v2/complete/sess_456

# Response:
{
  "session_id": "sess_456",
  "status": "completed",
  "total_questions": 5,
  "evaluation": {
    "overall_score": 7.83,
    "recommendation": "hire",
    "clarity": 8.2,
    "relevance": 8.4,
    "depth": 6.9
  },
  "conversation": [ ... ],
  "performance_metrics": {
    "avg_response_time": 2.45
  }
}
```

### Example 2: Streaming Question

```javascript
// JavaScript client
const sessionId = 'sess_456';
const eventSource = new EventSource(
  `http://localhost:8000/interview/v2/stream/${sessionId}`
);

let fullQuestion = '';

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.chunk) {
    fullQuestion += data.chunk;
    document.getElementById('question').innerText = fullQuestion;
  }
  
  if (data.done) {
    console.log('Complete question:', fullQuestion);
    eventSource.close();
  }
  
  if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('EventSource error:', error);
  eventSource.close();
};
```

### Example 3: Python Client

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Start session (with file uploads - recommended)
with open("resume.pdf", "rb") as cv, open("job_description.pdf", "rb") as jd:
    files = {
        "cv_file": cv,
        "jd_file": jd
    }
    data = {
        "user_id": "user_123",
        "session_id": "sess_789",
        "role": "Backend Engineer",
        "company": "StartupCo"
    }
    response = requests.post(
        f"{BASE_URL}/interview/v2/start-with-ids",
        files=files,
        data=data
    )
    print(f"First question: {response.json()['question']}")

# Alternative: Using direct text
response = requests.post(
    f"{BASE_URL}/interview/v2/start",
    json={
        "user_id": "user_123",
        "session_id": "sess_789",
        "role": "Backend Engineer",
        "company": "StartupCo",
        "cv_text": "John Doe\n5 years Python...",
        "jd_text": "Backend Engineer\nRequires Python..."
    }
)
print(f"First question: {response.json()['question']}")

# 2. Submit audio answer
with open("answer.wav", "rb") as audio:
    files = {"audio_file": audio}
    data = {"session_id": "sess_789"}
    response = requests.post(
        f"{BASE_URL}/interview/v2/answer",
        files=files,
        data=data
    )
    result = response.json()
    print(f"Evaluation: {result['evaluation']}")
    print(f"Next question: {result['question']}")

# 3. Get session state
response = requests.get(f"{BASE_URL}/interview/v2/state/sess_789")
state = response.json()
print(f"Progress: {state['question_count']} questions asked")
print(f"Stage: {state['stage']}")

# 4. Monitor performance
response = requests.get(f"{BASE_URL}/interview/v2/performance/sess_789")
metrics = response.json()
print(f"Avg response time: {metrics['response_times']['avg']:.2f}s")
```

### Example 4: Monitoring Dashboard

```python
import requests
import time

BASE_URL = "http://localhost:8000"

def monitor_system():
    """Monitor system performance"""
    response = requests.get(f"{BASE_URL}/interview/v2/metrics/global")
    metrics = response.json()["metrics"]
    
    print("\n=== System Performance ===")
    print(f"LLM Calls: {metrics['llm_calls']['total']}")
    print(f"Avg LLM Duration: {metrics['llm_calls']['avg_duration']:.2f}s")
    print(f"Cache Hit Rate: {metrics['cache']['hit_rate_percentage']}")
    print(f"API Avg Duration: {metrics['api_requests']['avg_duration']:.2f}s")
    
    # Check if performance is good
    if metrics['llm_calls']['avg_duration'] > 3.0:
        print("⚠️ Warning: LLM calls are slow!")
    
    if metrics['cache']['hit_rate'] < 0.5:
        print("⚠️ Warning: Low cache hit rate!")
    
    if metrics['cache']['hit_rate'] > 0.7:
        print("✅ Excellent cache performance!")

# Run every minute
while True:
    monitor_system()
    time.sleep(60)
```

---

## Best Practices

### 1. Use File Uploads or MongoDB IDs for Best Performance
```bash
# Best - File uploads with automatic text extraction
curl -X POST /interview/v2/start-with-ids \
  -F "cv_file=@resume.pdf" \
  -F "jd_file=@job_description.pdf"

# Good - MongoDB IDs enable caching
curl -X POST /interview/v2/start-with-ids \
  -F "cv_id=60d5ec49..." \
  -F "jd_id=60d5ec50..."

# Avoid - Direct text, no caching benefits
curl -X POST /interview/v2/start \
  -d '{"cv_text": "...", "jd_text": "..."}'
```

### 2. Monitor Performance Regularly
```bash
# Check global metrics
curl /interview/v2/metrics/global

# Check specific session
curl /interview/v2/performance/{session_id}
```

### 3. Use Streaming for Better UX
```javascript
// Progressive display vs. waiting
const stream = new EventSource('/interview/v2/stream/...');
```

### 4. Handle Errors Gracefully
```javascript
fetch('/interview/v2/answer', { ... })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'completed') {
      // Interview finished
      showCompletionPage();
    } else {
      // Show next question
      displayQuestion(data.question);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showErrorMessage();
  });
```

---

## Performance Targets

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| First question (cached) | < 3s | > 5s |
| First question (uncached) | < 6s | > 10s |
| Subsequent questions | < 3s | > 5s |
| Cache hit rate | > 60% | < 40% |
| LLM avg duration | < 2.5s | > 4s |

---

## Migration Checklist

- [ ] Update API base URL to `/interview/v2/`
- [ ] Change request format for start endpoint
- [ ] Update response parsing (new structure)
- [ ] Implement streaming support (optional)
- [ ] Add performance monitoring
- [ ] Test error handling
- [ ] Update documentation
- [ ] Monitor cache hit rate
- [ ] Compare performance metrics
- [ ] Gradual rollout to production

---

## Support & Troubleshooting

### Common Issues

**1. Slow responses despite caching**
- Check cache hit rate: `/interview/v2/metrics/global`
- Verify MongoDB connection
- Review logs for "SLOW LLM CALL" warnings

**2. Session not found errors**
- Check session expiry (24-hour TTL)
- Verify session_id is correct
- Check MongoDB connection

**3. Low cache hit rate**
- Ensure using MongoDB IDs, not raw text
- Check CV/JD ID consistency
- Verify cache TTL settings

**4. Audio transcription failures**
- Verify audio file format (wav, mp3, m4a)
- Check file size (< 10MB recommended)
- Ensure audio has actual content

**5. CV/JD file upload failures**
- Supported formats: PDF, DOCX, TXT
- Maximum file size: 10MB per file
- Ensure files are not corrupted
- Check file encoding (UTF-8 recommended for TXT)
- Verify files contain actual text content

**6. Validation errors: "user_id must be a string"**
- **Problem:** FastAPI Pydantic validation failing
- **Cause:** Missing `Content-Type: application/json` header
- **Solution:** Add `-H "Content-Type: application/json"` to your request
- **Wrong:** Sending form-data to `/v2/start` endpoint
- **Correct:** Send JSON to `/v2/start` OR form-data to `/v2/start-with-ids`

**Example Fix:**
```bash
# ❌ Wrong - Missing Content-Type header
curl -X POST http://localhost:8000/interview/v2/start -d '{...}'

# ✅ Correct - With proper header
curl -X POST http://localhost:8000/interview/v2/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_123", ...}'

# ✅ Alternative - Use start-with-ids for form-data
curl -X POST http://localhost:8000/interview/v2/start-with-ids \
  -F "user_id=user_123" \
  -F "session_id=sess_456" \
  -F "role=Engineer" \
  -F "company=TechCorp" \
  -F "cv_text=..." \
  -F "jd_text=..."
```

### Debug Endpoints

```bash
# Check session state
GET /interview/v2/state/{session_id}

# Check performance
GET /interview/v2/performance/{session_id}

# Global metrics
GET /interview/v2/metrics/global

# Health check
GET /healthz
```

---

## Changelog

### V2.0.0 (February 2026)
- ✅ Initial V2 release
- ✅ MongoDB caching implementation
- ✅ LangGraph workflow integration
- ✅ Streaming support via SSE
- ✅ Performance monitoring system
- ✅ Async/concurrent operations
- ✅ 60-70% performance improvement
- ✅ Comprehensive documentation

---

**Last Updated:** February 1, 2026  
**API Version:** 2.0  
**Base Path:** `/interview/v2/`  
**Status:** ✅ Production Ready
