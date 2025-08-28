#!/usr/bin/env python3
"""
Test script specifically for Groq integration
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cv_eval.engine import CVEvaluationEngine
from cv_eval.schemas import CVEvaluationRequest


def test_groq_integration():
    """Test Groq integration specifically"""
    
    # Test CV text
    cv_text = """
JOHN DOE
Software Engineer
john.doe@email.com | +1 (555) 123-4567 | linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years developing scalable web applications and microservices. Proficient in Python, JavaScript, and cloud technologies. Passionate about clean code, testing, and continuous improvement.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript, Java
Frameworks: FastAPI, Django, React, Node.js, Spring Boot
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, CI/CD
Tools: Git, JIRA, Confluence, Postman, VS Code

PROFESSIONAL EXPERIENCE

Senior Software Engineer | TechCorp Inc. | 2022 - Present
• Led development of microservices architecture serving 1M+ users
• Implemented Redis caching layer reducing API response time by 40%
• Mentored 3 junior developers and conducted code reviews
• Collaborated with product team to define technical requirements
• Technologies: Python, FastAPI, PostgreSQL, Redis, Docker, AWS

Software Engineer | StartupXYZ | 2020 - 2022
• Developed RESTful APIs using Django and Django REST Framework
• Built React frontend components with TypeScript and Material-UI
• Implemented automated testing achieving 90% code coverage
• Participated in agile development process with 2-week sprints
• Technologies: Python, Django, JavaScript, React, PostgreSQL

Junior Developer | WebDev Solutions | 2018 - 2020
• Created responsive web applications using HTML, CSS, and JavaScript
• Assisted in database design and optimization
• Fixed bugs and implemented new features based on client feedback
• Technologies: HTML, CSS, JavaScript, PHP, MySQL

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2014 - 2018
GPA: 3.8/4.0

CERTIFICATIONS
AWS Certified Developer Associate
Google Cloud Professional Developer
Scrum Master Certified (SMC)

PROJECTS
E-commerce Platform: Built full-stack application with Python backend and React frontend
Task Management App: Developed REST API with FastAPI and PostgreSQL
Weather Dashboard: Created real-time weather app using OpenWeather API and Chart.js

LANGUAGES
English (Native), Spanish (Conversational)

INTERESTS
Open source contribution, machine learning, hiking, reading technical blogs
"""

    # Test JD text
    jd_text = """
SENIOR SOFTWARE ENGINEER - BACKEND
TechCorp Inc. | San Francisco, CA | Full-time

ABOUT THE ROLE
We are seeking a Senior Software Engineer to join our backend team and help build scalable, high-performance systems that serve millions of users worldwide. You will work on challenging technical problems and collaborate with cross-functional teams to deliver exceptional user experiences.

RESPONSIBILITIES
• Design and implement scalable backend services and APIs
• Write clean, maintainable, and well-tested code
• Collaborate with frontend engineers, product managers, and designers
• Participate in code reviews and technical discussions
• Mentor junior developers and share knowledge with the team
• Contribute to architectural decisions and system design
• Monitor and optimize application performance
• Ensure code quality and maintain high test coverage

REQUIREMENTS
• 5+ years of software engineering experience
• Strong proficiency in Python, Java, or similar languages
• Experience with web frameworks (FastAPI, Django, Spring Boot)
• Knowledge of database design and optimization (PostgreSQL, MongoDB)
• Experience with cloud platforms (AWS, GCP, Azure)
• Understanding of microservices architecture
• Familiarity with containerization (Docker, Kubernetes)
• Experience with CI/CD pipelines and automated testing
• Strong problem-solving and analytical skills
• Excellent communication and collaboration abilities

PREFERRED QUALIFICATIONS
• Experience with high-traffic applications
• Knowledge of message queues and caching systems
• Experience with monitoring and observability tools
• Understanding of security best practices
• Contributions to open source projects
• Experience with agile development methodologies

TECHNOLOGY STACK
• Backend: Python, FastAPI, Django, Java, Spring Boot
• Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
• Cloud: AWS, Docker, Kubernetes, Terraform
• Testing: pytest, JUnit, Mockito
• Monitoring: Prometheus, Grafana, ELK Stack
• Version Control: Git, GitHub

COMPENSATION & BENEFITS
• Competitive salary range: $120,000 - $180,000
• Equity participation
• Comprehensive health, dental, and vision coverage
• 401(k) with company match
• Flexible work arrangements
• Professional development budget
• Unlimited PTO
• Team events and activities

CULTURE & VALUES
• Innovation and continuous learning
• Collaboration and knowledge sharing
• Work-life balance
• Diversity and inclusion
• Customer-focused development
• Quality and craftsmanship

APPLICATION PROCESS
1. Submit resume and cover letter
2. Technical phone screen
3. Take-home coding assignment
4. On-site technical interview
5. Team fit and culture interview
6. Reference checks
7. Offer and negotiation

CONTACT
For questions about this position, please contact:
recruiting@techcorp.com
+1 (555) 987-6543

TechCorp Inc. is an equal opportunity employer committed to diversity and inclusion in the workplace.
"""

    print("🚀 Testing Groq Integration for CV Evaluation")
    print("=" * 60)
    
    # Test 1: Without Groq API key (should use heuristic)
    print("\n1️⃣ Testing without Groq API key (heuristic fallback):")
    engine_no_groq = CVEvaluationEngine(use_llm=True)
    
    request = CVEvaluationRequest(
        cv_text=cv_text,
        jd_text=jd_text,
        include_constraints=True
    )
    
    result = engine_no_groq.evaluate(request)
    print(f"   Fit Index: {result.fit_index}/100 ({result.band})")
    print(f"   CV Quality: {result.cv_quality.overall_score}/100")
    print(f"   JD Match: {result.jd_match.overall_score}/100")
    
    if engine_no_groq.use_llm and engine_no_groq.llm_scorer:
        print("   ✅ Groq scorer initialized")
    else:
        print("   🔧 Using heuristic scoring (no Groq API key)")
    
    # Test 2: Test with mock Groq API key
    print("\n2️⃣ Testing with mock Groq API key:")
    
    # Temporarily set mock API key
    original_groq_key = os.environ.get('GROQ_API_KEY')
    os.environ['GROQ_API_KEY'] = 'mock-groq-key-for-testing'
    
    try:
        # This will fail to initialize Groq scorer but should fall back gracefully
        engine_mock = CVEvaluationEngine(use_llm=True)
        
        result = engine_mock.evaluate(request)
        print(f"   Fit Index: {result.fit_index}/100 ({result.band})")
        print(f"   CV Quality: {result.cv_quality.overall_score}/100")
        print(f"   JD Match: {result.jd_match.overall_score}/100")
        
        if engine_mock.use_llm and engine_mock.llm_scorer:
            print("   ✅ Groq scorer initialized with mock key")
        else:
            print("   🔧 Fallback to heuristic (mock key not valid)")
    
    finally:
        # Restore original environment
        if original_groq_key:
            os.environ['GROQ_API_KEY'] = original_groq_key
        else:
            os.environ.pop('GROQ_API_KEY', None)
    
    print("\n✅ Groq Integration Test Completed!")
    print("\n📝 To test with real Groq:")
    print("   1. Get your Groq API key from: https://console.groq.com/")
    print("   2. Set GROQ_API_KEY environment variable")
    print("   3. Run: python test_evaluation.py")
    print("   4. The system will automatically use Groq scoring if available")
    print("\n🔧 Available Groq models:")
    print("   - llama3-8b-8192 (default, fast)")
    print("   - llama3-70b-8192 (more capable)")
    print("   - mixtral-8x7b-32768 (balanced)")
    print("   - gemma2-9b-it (efficient)")


if __name__ == "__main__":
    test_groq_integration()
