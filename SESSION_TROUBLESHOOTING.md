# Session Not Found - Troubleshooting Guide

## Problem
```
ERROR: Session not found for user_id: xxx, session_id: xxx
```

## Root Cause
The interview system uses **in-memory session storage** which is lost when the server restarts.

## Solutions

### 1. Check Active Sessions
```bash
# Debug endpoint to see all active sessions
curl "http://34.27.237.113:8000/api/interview/debug/sessions"
```

### 2. Complete Flow Test
```bash
# Step 1: Start session
curl -X POST "http://34.27.237.113:8000/api/interview/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-001",
    "session_id": "session-001",
    "role_title": "Senior Backend Engineer",
    "company_name": "TechCorp Inc",
    "industry": "Technology",
    "cv": "Experienced Python developer with 5+ years",
    "jd": "Senior backend role requiring Python, Node.js",
    "round_type": "full"
  }'

# Step 2: Verify session exists
curl "http://34.27.237.113:8000/api/interview/state/test-user-001/session-001"

# Step 3: Submit voice answer (use EXACT same user_id and session_id)
curl -X POST "http://34.27.237.113:8000/api/interview/answer" \
  -F "user_id=test-user-001" \
  -F "session_id=session-001" \
  -F "audio_file=@test-audio.wav"
```

### 3. Session ID Matching
**CRITICAL**: Ensure exact same `user_id` and `session_id` in both start and answer calls:
- ✅ `user_id: "test-user-001"` (both calls)
- ✅ `session_id: "session-001"` (both calls)
- ❌ Different IDs will cause "Session not found"

### 4. Server Restart Issue
If server restarted between start and answer:
- All in-memory sessions are lost
- Must call `/start` again before `/answer`

### 5. Quick Test Script
```bash
#!/bin/bash
USER_ID="test-$(date +%s)"
SESSION_ID="session-$(date +%s)"

echo "Starting session with USER_ID=$USER_ID, SESSION_ID=$SESSION_ID"

# Start session
START_RESPONSE=$(curl -s -X POST "http://34.27.237.113:8000/api/interview/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"session_id\": \"$SESSION_ID\",
    \"role_title\": \"Backend Engineer\",
    \"company_name\": \"TestCorp\",
    \"industry\": \"Technology\",
    \"cv\": \"Test CV content\",
    \"jd\": \"Test JD content\",
    \"round_type\": \"full\"
  }")

echo "Start response: $START_RESPONSE"

# Check if session exists
echo "Checking session state..."
curl -s "http://34.27.237.113:8000/api/interview/state/$USER_ID/$SESSION_ID"

# Create dummy audio file for testing
echo "Creating test audio file..."
echo "test audio data" > test-audio.wav

# Submit answer
echo "Submitting voice answer..."
curl -X POST "http://34.27.237.113:8000/api/interview/answer" \
  -F "user_id=$USER_ID" \
  -F "session_id=$SESSION_ID" \
  -F "audio_file=@test-audio.wav"

# Cleanup
rm -f test-audio.wav
```

## Prevention

### Use Consistent Session Management
```javascript
// Frontend: Store session info after start
const sessionData = {
  user_id: "user-123",
  session_id: "session-123"
};

// Use EXACT same values for answer submission
const formData = new FormData();
formData.append('user_id', sessionData.user_id);
formData.append('session_id', sessionData.session_id);
formData.append('audio_file', audioBlob);
```

### Add Session Persistence (Future Enhancement)
```python
# TODO: Replace in-memory storage with database persistence
# self.sessions: Dict[str, InterviewState] = {}  # Current (volatile)
# Use MongoDB/Redis for persistent session storage
```

## Debug Commands

```bash
# 1. Check server status
curl "http://34.27.237.113:8000/healthz"

# 2. List all active sessions
curl "http://34.27.237.113:8000/api/interview/debug/sessions"

# 3. Check specific session
curl "http://34.27.237.113:8000/api/interview/state/USER_ID/SESSION_ID"

# 4. Test with minimal session
curl -X POST "http://34.27.237.113:8000/api/interview/start" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","session_id":"test","role_title":"Engineer","company_name":"Test","industry":"Tech"}'
```

## Error Messages Explained

- `Session not found` = Session never created or server restarted
- `Audio file is required` = Missing audio file in form data
- `Speech recognition failed` = Audio processing error
- `Internal server error` = Unexpected system error

**Solution**: Always start session first, then immediately submit answer with matching IDs.