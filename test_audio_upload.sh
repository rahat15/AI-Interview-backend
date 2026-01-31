#!/bin/bash
# Test script for V2 Interview API with Audio

BASE_URL="http://127.0.0.1:8000"

echo "=== V2 Interview API - Audio Test ==="
echo ""

# Step 1: Start interview
echo "1. Starting interview..."
START_RESPONSE=$(curl -s -X POST "$BASE_URL/v2/interview/start" \
  -F "role=Software Engineer" \
  -F "company=Test Corp" \
  -F "resume_text=John Doe, 5 years Python experience, built REST APIs" \
  -F "jd_text=Looking for Python developer with API experience")

echo "$START_RESPONSE" | jq '.'
SESSION_ID=$(echo "$START_RESPONSE" | jq -r '.session_id')

echo ""
echo "Session ID: $SESSION_ID"
echo ""

# Step 2: Check if audio file exists
if [ -f "/tmp/test_answer.wav" ]; then
  echo "2. Submitting AUDIO answer..."
  ANSWER_RESPONSE=$(curl -s -X POST "$BASE_URL/v2/interview/$SESSION_ID/answer" \
    -F "answer_audio=@/tmp/test_answer.wav")
  echo "$ANSWER_RESPONSE" | jq '.'
else
  echo "2. Submitting TEXT answer (no audio file found at /tmp/test_answer.wav)..."
  ANSWER_RESPONSE=$(curl -s -X POST "$BASE_URL/v2/interview/$SESSION_ID/answer" \
    -F "answer=I have 5 years of experience building REST APIs with Python and FastAPI")
  echo "$ANSWER_RESPONSE" | jq '.'
fi

echo ""
echo "3. Completing interview..."
COMPLETE_RESPONSE=$(curl -s -X POST "$BASE_URL/v2/interview/$SESSION_ID/complete" \
  -H "Content-Type: application/json" \
  -d '{"final_notes":"Test interview"}')

echo "$COMPLETE_RESPONSE" | jq '.voice_analytics'

echo ""
echo "=== Test Complete ==="
echo ""
echo "To test with REAL audio:"
echo "  1. Record a WAV file and save as /tmp/test_answer.wav"
echo "  2. Run this script again"
