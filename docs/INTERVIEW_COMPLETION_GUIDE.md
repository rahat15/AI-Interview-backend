# Interview Completion Guide

Complete guide on how interviews end and when to call the completion endpoint.

---

## How Interviews End

The V2 Interview API supports **3 ways** to complete an interview:

### 1. 🤖 **Automatic Completion** (NEW)

The system **automatically detects** when an interview should end based on:

#### Candidate Requests to End
If the candidate says any of these phrases:
- "end the interview"
- "finish the interview"  
- "stop the interview"
- "don't want to continue"
- "I want to end"
- "I want to stop"
- "that's all"
- "no more questions"

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/answer" \
  -F "answer=I don't want to continue this interview. Please end it."
```

**Response:**
```json
{
  "session_id": "96414eaf-11af-4b4b-8b03-e999489f45cf",
  "status": "completed",
  "question": "Okay, I understand. Thank you for your time today, Karman.",
  "question_number": 3,
  "completion_reason": "candidate_requested_end",
  "message": "Interview completed. Call /complete endpoint to get final evaluation."
}
```

#### Interviewer Concludes
If Gemini (the AI interviewer) says closing phrases like:
- "Thank you for your time"
- "Thanks for joining"
- "That concludes our interview"
- "We'll be in touch"
- "We'll get back to you"
- "That wraps up"
- "That's all the questions I have"

**Example Flow:**
```
Candidate: "I think I've covered everything about my experience."
Gemini: "Perfect! Thank you for your time today. We'll be in touch soon."
```

**Response:**
```json
{
  "session_id": "96414eaf-11af-4b4b-8b03-e999489f45cf",
  "status": "completed",
  "question": "Perfect! Thank you for your time today. We'll be in touch soon.",
  "question_number": 5,
  "completion_reason": "interviewer_concluded",
  "message": "Interview completed. Call /complete endpoint to get final evaluation."
}
```

#### Maximum Questions Reached
If the interview reaches **10 questions** (safety limit):

**Response:**
```json
{
  "session_id": "96414eaf-11af-4b4b-8b03-e999489f45cf",
  "status": "completed",
  "question": "...",
  "question_number": 10,
  "completion_reason": "max_questions_reached",
  "message": "Interview completed. Call /complete endpoint to get final evaluation."
}
```

---

### 2. 📞 **Manual Completion** (Original Method)

You can **manually end** the interview at any time by calling:

```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/complete" \
  -H "Content-Type: application/json" \
  -d '{"final_notes": "Optional notes here"}'
```

This is useful when:
- You want to end the interview at a specific point
- You're implementing your own completion logic
- You want to add custom final notes

---

### 3. 🔄 **Check Status Before Completion**

Always check the interview status to see if it's already completed:

```bash
curl "http://127.0.0.1:8000/v2/interview/$SESSION/status"
```

**Response when active:**
```json
{
  "session_id": "...",
  "status": "active",
  "question": "Can you tell me more about...",
  "question_number": 3,
  "history": [...]
}
```

**Response when auto-completed:**
```json
{
  "session_id": "...",
  "status": "completed",
  "question": "Thank you for your time!",
  "question_number": 5,
  "completion_reason": "interviewer_concluded",
  "history": [...]
}
```

---

## Complete End-to-End Flow

### Scenario 1: Auto-Completion Flow

```bash
#!/bin/bash

# 1. Start interview
SESSION=$(curl -s -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Software Engineer" \
  -F "company=TechCorp" \
  -F "resume_file=@resume.pdf" \
  -F "jd_file=@jd.pdf" | jq -r '.session_id')

echo "Session started: $SESSION"

# 2. Answer questions (loop until completed)
while true; do
  # Get current status
  STATUS=$(curl -s "http://127.0.0.1:8000/v2/interview/$SESSION/status" | jq -r '.status')
  
  if [ "$STATUS" == "completed" ]; then
    echo "Interview auto-completed!"
    break
  fi
  
  # Submit answer (could be text or audio)
  read -p "Your answer: " ANSWER
  
  RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/answer" \
    -F "answer=$ANSWER")
  
  # Check if this response completed the interview
  RESPONSE_STATUS=$(echo $RESPONSE | jq -r '.status')
  
  if [ "$RESPONSE_STATUS" == "completed" ]; then
    echo "Interview completed after this answer!"
    REASON=$(echo $RESPONSE | jq -r '.completion_reason')
    echo "Reason: $REASON"
    break
  fi
  
  # Show next question
  echo "Next question: $(echo $RESPONSE | jq -r '.question')"
done

# 3. Get final evaluation report
echo "Fetching final report..."
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/complete" \
  -H "Content-Type: application/json" \
  -d '{}' | jq . > interview_report.json

echo "Report saved to interview_report.json"
```

### Scenario 2: Manual Completion Flow

```bash
#!/bin/bash

SESSION=$(curl -s -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Data Scientist" \
  -F "company=AI Startup" \
  -F "resume_file=@resume.pdf" \
  -F "jd_file=@jd.pdf" | jq -r '.session_id')

# Answer 3 questions
for i in {1..3}; do
  curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/answer" \
    -F "answer=My answer to question $i..."
done

# Manually complete
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/complete" \
  -H "Content-Type: application/json" \
  -d '{"final_notes": "Candidate strong in Python"}' \
  | jq . > report.json
```

---

## Response Status Codes

### During Interview (Active)

**POST /answer** returns:
```json
{
  "status": "active",
  "question": "Next question here...",
  "question_number": 2
}
```

### Auto-Completion Detected

**POST /answer** returns:
```json
{
  "status": "completed",
  "question": "Final response from interviewer",
  "completion_reason": "candidate_requested_end",
  "message": "Interview completed. Call /complete endpoint to get final evaluation."
}
```

### Final Report

**POST /complete** returns:
```json
{
  "status": "completed",
  "evaluation": {
    "overall_score": 8,
    "recommendation": "hire",
    ...
  },
  "voice_analytics": {...},
  "video_analytics": {...},
  "conversation": [...]
}
```

---

## Completion Reasons Explained

| Reason | Trigger | Example |
|--------|---------|---------|
| `candidate_requested_end` | Candidate asks to stop | "I don't want to continue" |
| `interviewer_concluded` | AI says goodbye | "Thank you for your time!" |
| `max_questions_reached` | 10 questions asked | Auto-limit for safety |
| `manual` | `/complete` called directly | User triggers endpoint |

---

## Best Practices

### ✅ Recommended Flow

1. **Start the interview** with resume + JD
2. **Submit answers** one by one via `/answer`
3. **Check response status** after each answer:
   - If `"status": "active"` → continue
   - If `"status": "completed"` → proceed to step 4
4. **Call `/complete`** to get full evaluation report
5. **Save the report** for analysis

### ⚠️ Important Notes

- **Auto-completion is a signal, not the final report**
  - When `status: "completed"` appears, you MUST still call `/complete` to get the evaluation
  - The completion response only includes the final question, not the full analysis

- **Check status after every answer**
  - Don't assume the interview continues indefinitely
  - Status changes from `active` → `completed` when auto-triggered

- **Manual completion always works**
  - You can call `/complete` at any time, even if status is still `active`
  - Useful for time-limited interviews or custom logic

### 🚫 Common Mistakes

❌ **Calling `/answer` after completion**
```bash
# Wrong: trying to submit after completion
curl -X POST ".../answer" -F "answer=..."  # Will fail with 400
```

❌ **Not calling `/complete` to get evaluation**
```bash
# Wrong: stopping when status becomes "completed"
# You'll miss the full evaluation report!
```

✅ **Correct approach:**
```bash
# Check status
STATUS=$(curl -s ".../status" | jq -r '.status')

if [ "$STATUS" == "completed" ]; then
  # Get full report
  curl -X POST ".../complete" -H "Content-Type: application/json" -d '{}'
fi
```

---

## Frontend Integration Example

### React/TypeScript Example

```typescript
interface InterviewSession {
  sessionId: string;
  status: 'active' | 'completed';
  currentQuestion: string;
  questionNumber: number;
  completionReason?: string;
}

async function submitAnswer(
  sessionId: string, 
  answer: string
): Promise<InterviewSession> {
  const formData = new FormData();
  formData.append('answer', answer);
  
  const response = await fetch(
    `http://127.0.0.1:8000/v2/interview/${sessionId}/answer`,
    {
      method: 'POST',
      body: formData
    }
  );
  
  const data = await response.json();
  
  // Check if interview auto-completed
  if (data.status === 'completed') {
    console.log('Interview completed:', data.completion_reason);
    // Trigger final report fetch
    await fetchFinalReport(sessionId);
  }
  
  return {
    sessionId: data.session_id,
    status: data.status,
    currentQuestion: data.question,
    questionNumber: data.question_number,
    completionReason: data.completion_reason
  };
}

async function fetchFinalReport(sessionId: string) {
  const response = await fetch(
    `http://127.0.0.1:8000/v2/interview/${sessionId}/complete`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    }
  );
  
  const report = await response.json();
  console.log('Final evaluation:', report.evaluation);
  return report;
}

// Usage in component
const handleSubmitAnswer = async (answer: string) => {
  const result = await submitAnswer(currentSession.sessionId, answer);
  
  if (result.status === 'completed') {
    // Show completion UI
    setInterviewComplete(true);
    setCompletionReason(result.completionReason);
  } else {
    // Show next question
    setCurrentQuestion(result.currentQuestion);
  }
};
```

---

## Testing Auto-Completion

### Test 1: Candidate Ends Interview

```bash
SESSION=$(curl -s -X POST "http://127.0.0.1:8000/v2/interview/start" \
  -F "role=Engineer" -F "company=Test" \
  -F "resume_text=Test resume" -F "jd_text=Test JD" | jq -r '.session_id')

# Submit ending request
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/answer" \
  -F "answer=I want to end the interview now, thank you." | jq .

# Should return: "status": "completed", "completion_reason": "candidate_requested_end"
```

### Test 2: Verify Completion in Status

```bash
# After auto-completion
curl "http://127.0.0.1:8000/v2/interview/$SESSION/status" | jq '.status'
# Should return: "completed"
```

### Test 3: Get Final Report

```bash
curl -X POST "http://127.0.0.1:8000/v2/interview/$SESSION/complete" \
  -H "Content-Type: application/json" -d '{}' | jq '.evaluation.overall_score'
# Should return the evaluation score
```

---

## Summary

| Method | Trigger | When to Use | Requires /complete? |
|--------|---------|-------------|---------------------|
| Auto (Candidate) | "end the interview" | Natural user request | Yes |
| Auto (Interviewer) | "thank you for your time" | Natural conversation end | Yes |
| Auto (Max Questions) | 10 questions reached | Safety limit | Yes |
| Manual | Call `/complete` | Custom logic/timing | No (it IS the call) |

**Key Takeaway:** Auto-completion **signals** the interview end, but you must **call `/complete`** to get the full evaluation report!
