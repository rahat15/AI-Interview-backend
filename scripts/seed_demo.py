#!/usr/bin/env python3
"""
Demo seeding script for Interview Coach API
Creates sample users, CV/JD artifacts, and a demo interview session
"""

import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import get_db_context
from core.models import User, Artifact, Session, Question, Answer, Score, Report
from apps.api.deps.auth import get_password_hash
from interview.question import get_question_generator
from interview.evaluate.judge import get_llm_judge_evaluator


def create_demo_user(db):
    """Create a demo user"""
    # Check if demo user already exists
    existing_user = db.query(User).filter(User.email == "demo@example.com").first()
    if existing_user:
        print("Demo user already exists")
        return existing_user
    
    # Create demo user
    demo_user = User(
        email="demo@example.com",
        hashed_password=get_password_hash("demo123"),
        full_name="Demo User",
        is_active=True,
        is_superuser=False
    )
    
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    
    print(f"Created demo user: {demo_user.email}")
    return demo_user


def create_sample_cv(db):
    """Create a sample CV artifact"""
    cv_text = """
John Doe - Senior Backend Engineer

EXPERIENCE
Senior Backend Engineer at TechCorp (2020-2024)
- Led development of microservices architecture serving 1M+ users
- Implemented Redis caching layer reducing API response time by 40%
- Managed team of 5 developers and mentored junior engineers
- Used Python, FastAPI, PostgreSQL, Redis, AWS

Backend Developer at StartupXYZ (2018-2020)
- Built RESTful APIs using Django and Django REST Framework
- Implemented authentication system with JWT tokens
- Worked with PostgreSQL and MongoDB databases
- Deployed applications using Docker and Kubernetes

EDUCATION
Bachelor of Science in Computer Science
University of Technology, 2018

SKILLS
Python, FastAPI, Django, PostgreSQL, Redis, AWS, Docker, Kubernetes, Git, Agile
    """
    
    cv_artifact = Artifact(
        type="cv",
        path="/samples/sample_cv.txt",
        text=cv_text.strip(),
        meta={
            "normalized_data": {
                "personal_info": {"name": "John Doe", "email": "john@example.com"},
                "experience": [
                    {"title": "Senior Backend Engineer", "company": "TechCorp", "duration": "2020-2024"},
                    {"title": "Backend Developer", "company": "StartupXYZ", "duration": "2018-2020"}
                ],
                "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "AWS", "Docker", "Kubernetes"],
                "education": [{"degree": "Bachelor of Science in Computer Science", "institution": "University of Technology"}]
            }
        }
    )
    
    db.add(cv_artifact)
    db.commit()
    db.refresh(cv_artifact)
    
    print(f"Created sample CV artifact: {cv_artifact.id}")
    return cv_artifact


def create_sample_jd(db):
    """Create a sample job description artifact"""
    jd_text = """
Senior Backend Engineer - TechCorp Inc.

We are looking for a Senior Backend Engineer to join our growing team. You will be responsible for designing, building, and maintaining scalable backend services.

RESPONSIBILITIES
- Design and implement scalable microservices architecture
- Write clean, maintainable, and efficient code
- Collaborate with cross-functional teams to define and implement new features
- Mentor junior developers and conduct code reviews
- Optimize application performance and scalability
- Ensure code quality through testing and best practices

REQUIREMENTS
- 5+ years of experience in backend development
- Strong proficiency in Python and modern web frameworks
- Experience with microservices architecture
- Knowledge of PostgreSQL, Redis, and other databases
- Experience with cloud platforms (AWS, GCP, or Azure)
- Familiarity with Docker and Kubernetes
- Strong problem-solving and communication skills

BENEFITS
- Competitive salary and equity
- Health, dental, and vision insurance
- Flexible work arrangements
- Professional development opportunities
    """
    
    jd_artifact = Artifact(
        type="jd",
        path="/samples/sample_jd.txt",
        text=jd_text.strip(),
        meta={
            "normalized_data": {
                "job_title": "Senior Backend Engineer",
                "company_info": {"name": "TechCorp Inc"},
                "requirements": [
                    "5+ years of experience in backend development",
                    "Strong proficiency in Python and modern web frameworks",
                    "Experience with microservices architecture"
                ],
                "responsibilities": [
                    "Design and implement scalable microservices architecture",
                    "Write clean, maintainable, and efficient code"
                ]
            }
        }
    )
    
    db.add(jd_artifact)
    db.commit()
    db.refresh(jd_artifact)
    
    print(f"Created sample JD artifact: {jd_artifact.id}")
    return jd_artifact


def create_demo_session(db, user, cv_artifact, jd_artifact):
    """Create a demo interview session"""
    # Check if demo session already exists
    existing_session = db.query(Session).filter(
        Session.user_id == user.id,
        Session.role == "Senior Backend Engineer"
    ).first()
    
    if existing_session:
        print("Demo session already exists")
        return existing_session
    
    # Create demo session
    demo_session = Session(
        user_id=user.id,
        role="Senior Backend Engineer",
        industry="Technology",
        company="TechCorp Inc",
        status="active",
        cv_file_id=cv_artifact.id,
        jd_file_id=jd_artifact.id,
        current_question_index=0,
        total_questions=5
    )
    
    db.add(demo_session)
    db.commit()
    db.refresh(demo_session)
    
    print(f"Created demo session: {demo_session.id}")
    return demo_session


def create_sample_questions(db, session):
    """Create sample questions for the demo session"""
    questions_data = [
        {
            "competency": "technical",
            "difficulty": "medium",
            "text": "Can you walk me through a technical challenge you faced in your previous role as a Senior Backend Engineer? What was the problem, how did you approach it, and what was the outcome?",
            "order_index": 0,
            "meta": {
                "expected_signals": [
                    "Problem identification and analysis",
                    "Technical solution design",
                    "Implementation approach",
                    "Results and impact measurement"
                ],
                "pitfalls": [
                    "Vague problem description",
                    "No technical details",
                    "Missing outcome/results"
                ]
            }
        },
        {
            "competency": "leadership",
            "difficulty": "hard",
            "text": "Tell me about a time when you had to lead a team through a major change or transition. How did you approach it?",
            "order_index": 1,
            "meta": {
                "expected_signals": [
                    "Change management approach",
                    "Team communication",
                    "Stakeholder management",
                    "Results and impact"
                ],
                "pitfalls": [
                    "No change management strategy",
                    "Poor communication",
                    "No measurable results"
                ]
            }
        },
        {
            "competency": "problem_solving",
            "difficulty": "medium",
            "text": "How would you design a scalable system to handle high-traffic data processing? Walk me through your architecture decisions.",
            "order_index": 2,
            "meta": {
                "expected_signals": [
                    "System design principles",
                    "Scalability considerations",
                    "Technology choices",
                    "Trade-off analysis"
                ],
                "pitfalls": [
                    "Over-engineering",
                    "No scalability discussion",
                    "Missing trade-offs"
                ]
            }
        },
        {
            "competency": "communication",
            "difficulty": "easy",
            "text": "How do you explain complex technical concepts to non-technical stakeholders?",
            "order_index": 3,
            "meta": {
                "expected_signals": [
                    "Audience adaptation",
                    "Simplification skills",
                    "Examples usage",
                    "Feedback incorporation"
                ],
                "pitfalls": [
                    "Technical jargon",
                    "No audience consideration",
                    "No examples"
                ]
            }
        },
        {
            "competency": "behavioral",
            "difficulty": "medium",
            "text": "Describe a situation where you had to meet a tight deadline. How did you prioritize and manage your work?",
            "order_index": 4,
            "meta": {
                "expected_signals": [
                    "Time management",
                    "Prioritization skills",
                    "Communication with stakeholders",
                    "Quality maintenance"
                ],
                "pitfalls": [
                    "No prioritization strategy",
                    "Quality compromise",
                    "No stakeholder communication"
                ]
            }
        }
    ]
    
    questions = []
    for q_data in questions_data:
        question = Question(
            session_id=session.id,
            **q_data
        )
        db.add(question)
        questions.append(question)
    
    db.commit()
    
    print(f"Created {len(questions)} sample questions")
    return questions


def create_sample_answers(db, session, questions):
    """Create sample answers for the demo session"""
    sample_answers = [
        "In my previous role at TechCorp, I faced a challenge where our API response times were increasing due to database query performance issues. I started by analyzing the slow queries using database monitoring tools and identified that certain joins were causing bottlenecks. I implemented Redis caching for frequently accessed data and optimized the database queries by adding proper indexes. This resulted in a 40% reduction in API response times and improved user experience significantly.",
        
        "When our company decided to migrate from a monolithic architecture to microservices, I led a team of 5 developers through this transition. I began by creating a detailed migration plan and communicating the benefits and challenges to the team. I organized training sessions on microservices best practices and set up regular check-ins to address concerns. We successfully migrated three core services within 6 months, and the team became more confident with the new architecture.",
        
        "For a high-traffic data processing system, I would start with a distributed architecture using message queues like Apache Kafka for data ingestion. I'd implement horizontal scaling with multiple processing nodes and use Redis for caching frequently accessed data. I'd choose PostgreSQL for structured data and consider NoSQL solutions like MongoDB for flexible schema requirements. The key trade-offs would be between consistency and availability, and I'd implement eventual consistency patterns where appropriate.",
        
        "I adapt my communication based on the stakeholder's background. For executives, I focus on business impact and high-level architecture. I use analogies and visual diagrams to explain complex concepts, like comparing a microservices architecture to a restaurant kitchen where different chefs handle different dishes. I always ask for feedback to ensure understanding and adjust my explanation accordingly.",
        
        "When I had to deliver a critical feature within a tight deadline, I first assessed the scope and identified what was truly essential versus nice-to-have. I broke down the work into smaller, manageable tasks and estimated effort for each. I communicated the timeline and potential risks to stakeholders early and set up daily check-ins. I maintained code quality by writing tests and doing code reviews, even under time pressure."
    ]
    
    answers = []
    for i, (question, answer_text) in enumerate(zip(questions, sample_answers)):
        answer = Answer(
            session_id=session.id,
            question_id=question.id,
            text=answer_text,
            meta={"sample_answer": True}
        )
        db.add(answer)
        answers.append(answer)
    
    db.commit()
    
    print(f"Created {len(answers)} sample answers")
    return answers


def create_sample_scores(db, answers, questions):
    """Create sample scores for the demo answers"""
    evaluator = get_llm_judge_evaluator()
    
    scores = []
    for answer, question in zip(answers, questions):
        # Evaluate the answer
        evaluation = evaluator.evaluate_answer(
            answer_text=answer.text,
            question_meta=question.meta
        )
        
        # Create score record
        score = Score(
            answer_id=answer.id,
            rubric_json=evaluation.dict(),
            clarity=evaluation.scores.clarity,
            structure=evaluation.scores.structure,
            depth_specificity=evaluation.scores.depth_specificity,
            role_fit=evaluation.scores.role_fit,
            technical=evaluation.scores.technical,
            communication=evaluation.scores.communication,
            ownership=evaluation.scores.ownership,
            total_score=evaluation.scores.total_score,
            meta={"sample_score": True}
        )
        
        db.add(score)
        scores.append(score)
    
    db.commit()
    
    print(f"Created {len(scores)} sample scores")
    return scores


def create_sample_report(db, session, scores):
    """Create a sample report for the demo session"""
    # Check if report already exists
    existing_report = db.query(Report).filter(Report.session_id == session.id).first()
    if existing_report:
        print("Sample report already exists")
        return existing_report
    
    # Calculate overall score
    total_score = sum(score.total_score for score in scores) / len(scores) if scores else 0.0
    
    # Generate report data
    report_data = {
        "overall_score": total_score,
        "competency_breakdown": {
            "technical": 4.2,
            "leadership": 4.0,
            "problem_solving": 4.1,
            "communication": 4.3,
            "behavioral": 4.0
        },
        "strengths": [
            "Strong technical problem-solving skills",
            "Clear communication and explanation abilities",
            "Good understanding of system design principles",
            "Effective leadership and team management"
        ],
        "areas_for_improvement": [
            "Could provide more specific metrics in some responses",
            "Consider discussing trade-offs more explicitly",
            "Some answers could benefit from more detailed examples"
        ],
        "recommendations": [
            "Continue building on technical leadership skills",
            "Practice quantifying impact with specific metrics",
            "Consider taking on more complex architectural challenges"
        ]
    }
    
    report = Report(
        session_id=session.id,
        json=report_data,
        summary="Strong candidate with excellent technical skills and leadership potential. Demonstrates clear communication and problem-solving abilities.",
        overall_score=total_score,
        strengths=report_data["strengths"],
        areas_for_improvement=report_data["areas_for_improvement"],
        recommendations=report_data["recommendations"]
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    print(f"Created sample report: {report.id}")
    return report


def main():
    """Main seeding function"""
    print("Starting demo data seeding...")
    
    try:
        with get_db_context() as db:
            # Create demo user
            user = create_demo_user(db)
            
            # Create sample artifacts
            cv_artifact = create_sample_cv(db)
            jd_artifact = create_sample_jd(db)
            
            # Create demo session
            session = create_demo_session(db, user, cv_artifact, jd_artifact)
            
            # Create sample questions
            questions = create_sample_questions(db, session)
            
            # Create sample answers
            answers = create_sample_answers(db, session, questions)
            
            # Create sample scores
            scores = create_sample_scores(db, answers, questions)
            
            # Create sample report
            report = create_sample_report(db, session, scores)
            
            print("\nDemo data seeding completed successfully!")
            print(f"Demo user: {user.email} (password: demo123)")
            print(f"Demo session: {session.id}")
            print(f"Sample CV: {cv_artifact.id}")
            print(f"Sample JD: {jd_artifact.id}")
            print(f"Questions created: {len(questions)}")
            print(f"Answers created: {len(answers)}")
            print(f"Scores created: {len(scores)}")
            print(f"Report created: {report.id}")
            
    except Exception as e:
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
