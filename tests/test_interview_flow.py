
import requests
import json
import time
import os

BASE_URL = "http://localhost:8080"
AUDIO_FILE_PATH = "/Volumes/Data/ai-interview-rahat/test.mp3"

def test_interview_flow():
    print(f"Testing Interview Flow at {BASE_URL}")

    # 1. Health Check
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("Make sure the server is running on port 8000")
        return

    # 2. Start Interview Session
    user_id = "test_user_123"
    session_id = f"test_session_{int(time.time())}"
    
    start_payload = {
        "user_id": user_id,
        "session_id": session_id,
        "role_title": "Python Developer",
        "company_name": "Tech Corp",
        "industry": "Technology"
    }

    print(f"\nStarting Interview Session (ID: {session_id})...")
    response = requests.post(f"{BASE_URL}/v1/interview/start", json=start_payload)
    if response.status_code != 200:
        print(f"❌ Failed to start interview: {response.status_code} - {response.text}")
        return
    else:
        print("✅ Interview session started")
        # print(f"Response: {json.dumps(response.json(), indent=2)}")
        first_question = response.json().get("first_question")
        print(f"First Question: {first_question}")

    # 3. Simulate answering questions
    rounds_to_test = 2
    
    if not os.path.exists(AUDIO_FILE_PATH):
        print(f"⚠️ Warning: Audio file not found at {AUDIO_FILE_PATH}. Skipping answer submission test.")
        return

    for i in range(rounds_to_test):
        print(f"\n--- Round {i+1} ---")
        
        # Prepare multipart/form-data upload
        with open(AUDIO_FILE_PATH, "rb") as audio_file:
            files = {
                "audio_file": ("test.mp3", audio_file, "audio/mpeg")
            }
            data = {
                "user_id": user_id,
                "session_id": session_id
            }
            
            print("Submitting answer...")
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/v1/interview/answer", data=data, files=files)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Answer submittted in {duration:.2f}s")
                
                next_q = result.get("next_question")
                if next_q:
                    print(f"Next Question: {next_q}")
                else:
                    print("No next question (End of interview?)")
                    
                tech_eval = result.get("technical", {})
                print(f"Technical Depth: {tech_eval.get('technical_depth')}")
                print(f"Feedback: {result.get('evaluation', {}).get('feedback')}")
            else:
                print(f"❌ Failed to submit answer: {response.status_code} - {response.text}")
                break

    # 4. Generate Report
    print(f"\nGenerating Report for {session_id}...")
    response = requests.get(f"{BASE_URL}/v1/interview/report/{user_id}/{session_id}")
    if response.status_code == 200:
        report = response.json()
        print("✅ Report generated successfully")
        print(f"Average Scores: {json.dumps(report.get('avg_scores'), indent=2)}")
    else:
        print(f"❌ Failed to generate report: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_interview_flow()
