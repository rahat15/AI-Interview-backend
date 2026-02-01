
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_interview_flow():
    print(f"Testing Interview Flow at {BASE_URL}")

    # 1. Health Check
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # 2. Start Interview Session
    # Using a dummy user_id and session_id for testing
    user_id = "test_user_123"
    session_id = "test_session_456"
    
    start_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "role_title": "Python Developer",
        "company_name": "Tech Corp",
        "industry": "Technology"
    }

    print("\nStarting Interview Session...")
    response = requests.post(f"{BASE_URL}/v1/interview/start", json=start_payload)
    if response.status_code != 200:
        print(f"❌ Failed to start interview: {response.status_code} - {response.text}")
        return
    else:
        print("✅ Interview session started")
        print(f"Response: {response.json()}")

    # 3. Simulate answering a few questions
    # We will simulate 3 rounds of QA
    for i in range(3):
        print(f"\n--- Round {i+1} ---")
        
        # Get current state to know the question (optional, as start/answer returns it)
        state_response = requests.get(f"{BASE_URL}/v1/interview/state/{user_id}/{session_id}")
        if state_response.status_code == 200:
             state_data = state_response.json()
             current_question = state_data.get("history", [])[-1]["question"] if state_data.get("history") else "No question found"
             print(f"Current Question: {current_question}")
        
        # Answer the question
        answer_payload = {
             "user_id": user_id,
             "session_id": session_id,
             "answer_text": "I am a skilled Python developer with experience in FastAPI and Django. I have built scalable web applications and worked with microservices.",
             "audio_enabled": False 
             # Note: logic might depend on how answer is submitted (audio vs text). 
             # Check API_STRUCTURE again. It says /answer submits audio answer. 
             # Implementation of POST /v1/interview/answer in interview_routes.py needs checking.
             # Assuming we can send text answer for testing or need to mock audio.
             # Let's check interview_routes.py if it supports text answer directly or verify logic.
             # The implementation plan mentioned sending dummy audio/text.
        }
        
        # Wait, the API_STRUCTURE says /v1/interview/answer is for "Submit audio answer"
        # but /v1/sessions/{id}/answer is "Submit text answer".
        # Let's verify if /v1/interview/answer supports text only.
        # I will check interview_routes.py content first to be sure.
        
        # For now, I will pause writing the full loop until I check interview_routes.py
        pass

if __name__ == "__main__":
    test_interview_flow()
