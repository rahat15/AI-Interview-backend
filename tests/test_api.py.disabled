import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.models import User, Session as SessionModel, Artifact, Question, Answer, Score
from apps.api.deps.auth import get_password_hash


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user(self, client: TestClient, db_session: Session):
        """Test user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post("/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_login_user(self, client: TestClient, db_session: Session):
        """Test user login"""
        # Create a user first
        user = User(
            email="loginuser@example.com",
            hashed_password=get_password_hash("loginpassword123"),
            full_name="Login User"
        )
        db_session.add(user)
        db_session.commit()
        
        login_data = {
            "username": "loginuser@example.com",
            "password": "loginpassword123"
        }
        
        response = client.post("/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_get_current_user(self, client: TestClient, db_session: Session):
        """Test getting current user info"""
        # Create a user and get token
        user = User(
            email="currentuser@example.com",
            hashed_password=get_password_hash("currentpassword123"),
            full_name="Current User"
        )
        db_session.add(user)
        db_session.commit()
        
        login_data = {
            "username": "currentuser@example.com",
            "password": "currentpassword123"
        }
        
        login_response = client.post("/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name


class TestSessionEndpoints:
    """Test session management endpoints"""
    
    def test_create_session(self, client: TestClient, db_session: Session):
        """Test creating a new interview session"""
        # Create user and get token
        user = User(
            email="sessionuser@example.com",
            hashed_password=get_password_hash("sessionpassword123"),
            full_name="Session User"
        )
        db_session.add(user)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "sessionuser@example.com",
            "password": "sessionpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        session_data = {
            "role": "Software Engineer",
            "industry": "Technology",
            "company": "TestCorp"
        }
        
        with patch('interview.graph.InterviewGraph.create_plan') as mock_plan:
            mock_plan.return_value = {
                "total_questions": 10,
                "competencies": ["technical", "behavioral"],
                "estimated_duration": 45
            }
            
            response = client.post("/v1/sessions", json=session_data, headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["role"] == session_data["role"]
            assert data["industry"] == session_data["industry"]
            assert data["company"] == session_data["company"]
            assert data["status"] == "planned"
            assert "id" in data
    
    def test_get_session(self, client: TestClient, db_session: Session):
        """Test getting a specific session"""
        # Create user, session and get token
        user = User(
            email="getsessionuser@example.com",
            hashed_password=get_password_hash("getsessionpassword123"),
            full_name="Get Session User"
        )
        db_session.add(user)
        db_session.commit()
        
        session = SessionModel(
            user_id=user.id,
            role="Software Engineer",
            industry="Technology",
            company="TestCorp",
            status="planned"
        )
        db_session.add(session)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "getsessionuser@example.com",
            "password": "getsessionpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/v1/sessions/{session.id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(session.id)
        assert data["role"] == session.role
    
    def test_get_next_question(self, client: TestClient, db_session: Session):
        """Test getting the next question in a session"""
        # Create user, session, question and get token
        user = User(
            email="nextquestionuser@example.com",
            hashed_password=get_password_hash("nextquestionpassword123"),
            full_name="Next Question User"
        )
        db_session.add(user)
        db_session.commit()
        
        session = SessionModel(
            user_id=user.id,
            role="Software Engineer",
            industry="Technology",
            company="TestCorp",
            status="in_progress"
        )
        db_session.add(session)
        db_session.commit()
        
        question = Question(
            session_id=session.id,
            competency="technical",
            difficulty="medium",
            text="What is the time complexity of binary search?",
            meta={"signals_expected": ["algorithmic thinking"], "pitfalls": ["not considering edge cases"]}
        )
        db_session.add(question)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "nextquestionuser@example.com",
            "password": "nextquestionpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/v1/sessions/{session.id}/next-question", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["question_id"] == str(question.id)
        assert data["text"] == question.text
        assert data["competency"] == question.competency
        assert data["difficulty"] == question.difficulty
    
    def test_submit_answer(self, client: TestClient, db_session: Session):
        """Test submitting an answer to a question"""
        # Create user, session, question and get token
        user = User(
            email="submitansweruser@example.com",
            hashed_password=get_password_hash("submitanswerpassword123"),
            full_name="Submit Answer User"
        )
        db_session.add(user)
        db_session.commit()
        
        session = SessionModel(
            user_id=user.id,
            role="Software Engineer",
            industry="Technology",
            company="TestCorp",
            status="in_progress"
        )
        db_session.add(session)
        db_session.commit()
        
        question = Question(
            session_id=session.id,
            competency="technical",
            difficulty="medium",
            text="What is the time complexity of binary search?",
            meta={"signals_expected": ["algorithmic thinking"], "pitfalls": ["not considering edge cases"]}
        )
        db_session.add(question)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "submitansweruser@example.com",
            "password": "submitanswerpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        answer_data = {
            "question_id": str(question.id),
            "text": "Binary search has O(log n) time complexity because it divides the search space in half with each iteration."
        }
        
        with patch('apps.worker.jobs.enqueue_scoring_job') as mock_enqueue:
            mock_enqueue.return_value = "job-123"
            
            response = client.post(f"/v1/sessions/{session.id}/answer", json=answer_data, headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == "Answer submitted successfully"
            assert data["job_id"] == "job-123"
    
    def test_get_session_report(self, client: TestClient, db_session: Session):
        """Test getting a session report"""
        # Create user, session, questions, answers, scores and get token
        user = User(
            email="reportuser@example.com",
            hashed_password=get_password_hash("reportpassword123"),
            full_name="Report User"
        )
        db_session.add(user)
        db_session.commit()
        
        session = SessionModel(
            user_id=user.id,
            role="Software Engineer",
            industry="Technology",
            company="TestCorp",
            status="completed"
        )
        db_session.add(session)
        db_session.commit()
        
        question = Question(
            session_id=session.id,
            competency="technical",
            difficulty="medium",
            text="What is the time complexity of binary search?",
            meta={"signals_expected": ["algorithmic thinking"], "pitfalls": ["not considering edge cases"]}
        )
        db_session.add(question)
        db_session.commit()
        
        answer = Answer(
            session_id=session.id,
            question_id=question.id,
            text="Binary search has O(log n) time complexity.",
            meta={}
        )
        db_session.add(answer)
        db_session.commit()
        
        score = Score(
            answer_id=answer.id,
            rubric_json={
                "scores": {
                    "clarity": 4.0,
                    "structure": 3.5,
                    "depth_specificity": 4.0,
                    "role_fit": 4.5,
                    "technical": 4.0,
                    "communication": 4.0,
                    "ownership": 3.5
                },
                "rationale": "Good technical explanation with clear structure",
                "action_items": ["Provide more specific examples"],
                "exemplar_snippet": None,
                "meta": {}
            },
            clarity=4.0,
            structure=3.5,
            depth_specificity=4.0,
            role_fit=4.5,
            technical=4.0,
            communication=4.0,
            ownership=3.5
        )
        db_session.add(score)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "reportuser@example.com",
            "password": "reportpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get(f"/v1/sessions/{session.id}/report", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == str(session.id)
        assert data["status"] == "completed"
        assert "summary" in data
        assert "detailed_scores" in data
        assert "recommendations" in data


class TestUploadEndpoints:
    """Test file upload endpoints"""
    
    def test_upload_cv(self, client: TestClient, db_session: Session, tmp_path):
        """Test CV file upload"""
        # Create user and get token
        user = User(
            email="uploadcvuser@example.com",
            hashed_password=get_password_hash("uploadcvpassword123"),
            full_name="Upload CV User"
        )
        db_session.add(user)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "uploadcvuser@example.com",
            "password": "uploadcvpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test CV file
        cv_content = "John Doe\nSoftware Engineer\n5 years experience\nPython, JavaScript"
        cv_file = tmp_path / "test_cv.txt"
        cv_file.write_text(cv_content)
        
        with open(cv_file, "rb") as f:
            files = {"file": ("test_cv.txt", f, "text/plain")}
            response = client.post("/v1/uploads/cv", files=files, headers=headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "artifact_id" in data
        assert data["message"] == "CV uploaded successfully"
    
    def test_upload_jd(self, client: TestClient, db_session: Session, tmp_path):
        """Test JD file upload"""
        # Create user and get token
        user = User(
            email="uploadjduser@example.com",
            hashed_password=get_password_hash("uploadjdpassword123"),
            full_name="Upload JD User"
        )
        db_session.add(user)
        db_session.commit()
        
        login_response = client.post("/v1/auth/login", data={
            "username": "uploadjduser@example.com",
            "password": "uploadjdpassword123"
        })
        token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a test JD file
        jd_content = "Software Engineer Position\nRequirements: Python, 3+ years experience\nResponsibilities: Develop web applications"
        jd_file = tmp_path / "test_jd.txt"
        jd_file.write_text(jd_content)
        
        with open(jd_file, "rb") as f:
            files = {"file": ("test_jd.txt", f, "text/plain")}
            response = client.post("/v1/uploads/jd", files=files, headers=headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "artifact_id" in data
        assert data["message"] == "JD uploaded successfully"


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/healthz")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestErrorHandling:
    """Test error handling and validation"""
    
    def test_invalid_json_422(self, client: TestClient):
        """Test 422 error for invalid JSON"""
        response = client.post("/v1/sessions", data="invalid json")
        assert response.status_code == 422
    
    def test_unauthorized_401(self, client: TestClient):
        """Test 401 error for unauthorized access"""
        response = client.get("/v1/sessions")
        assert response.status_code == 401
    
    def test_not_found_404(self, client: TestClient):
        """Test 404 error for non-existent resource"""
        response = client.get(f"/v1/sessions/{uuid.uuid4()}")
        assert response.status_code == 404
