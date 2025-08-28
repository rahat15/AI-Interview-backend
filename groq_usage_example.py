#!/usr/bin/env python3
"""
Example usage of Groq for CV evaluation
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cv_eval.engine import CVEvaluationEngine
from cv_eval.schemas import CVEvaluationRequest


def example_groq_usage():
    """Example of using Groq for CV evaluation"""
    
    # Sample CV and JD text (shortened for example)
    cv_text = """
JOHN DOE
Software Engineer
john.doe@email.com | +1 (555) 123-4567

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years developing scalable web applications. 
Proficient in Python, JavaScript, and cloud technologies.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, TypeScript, Java
Frameworks: FastAPI, Django, React, Node.js
Databases: PostgreSQL, MongoDB, Redis
Cloud & DevOps: AWS, Docker, Kubernetes

PROFESSIONAL EXPERIENCE
Senior Software Engineer | TechCorp Inc. | 2022 - Present
• Led development of microservices architecture serving 1M+ users
• Implemented Redis caching layer reducing API response time by 40%
• Mentored 3 junior developers and conducted code reviews
• Technologies: Python, FastAPI, PostgreSQL, Redis, Docker, AWS

Software Engineer | StartupXYZ | 2020 - 2022
• Developed RESTful APIs using Django and Django REST Framework
• Built React frontend components with TypeScript and Material-UI
• Implemented automated testing achieving 90% code coverage
• Technologies: Python, Django, JavaScript, React, PostgreSQL

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2014 - 2018
GPA: 3.8/4.0

CERTIFICATIONS
AWS Certified Developer Associate
Google Cloud Professional Developer
"""

    jd_text = """
SENIOR SOFTWARE ENGINEER - BACKEND
TechCorp Inc. | San Francisco, CA | Full-time

ABOUT THE ROLE
We are seeking a Senior Software Engineer to join our backend team and help build scalable, 
high-performance systems that serve millions of users worldwide.

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

TECHNOLOGY STACK
• Backend: Python, FastAPI, Django, Java, Spring Boot
• Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
• Cloud: AWS, Docker, Kubernetes, Terraform
• Testing: pytest, JUnit, Mockito
• Monitoring: Prometheus, Grafana, ELK Stack
• Version Control: Git, GitHub
"""

    print("🚀 Groq CV Evaluation Example")
    print("=" * 50)
    
    # Check if Groq API key is available
    groq_api_key = os.environ.get('GROQ_API_KEY')
    
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("   Please set your Groq API key:")
        print("   Windows: set GROQ_API_KEY=your_api_key_here")
        print("   Linux/Mac: export GROQ_API_KEY=your_api_key_here")
        print("   Or add to .env file: GROQ_API_KEY=your_api_key_here")
        print("\n   Get your API key from: https://console.groq.com/")
        return
    
    print("✅ GROQ_API_KEY found in environment")
    
    # Initialize engine with Groq provider
    print("\n🔧 Initializing CV evaluation engine with Groq...")
    engine = CVEvaluationEngine(use_llm=True)
    
    if not engine.use_llm or not engine.llm_scorer:
        print("❌ Failed to initialize Groq scorer")
        return
    
    print("✅ Groq scorer initialized successfully")
    
    # Create evaluation request
    request = CVEvaluationRequest(
        cv_text=cv_text,
        jd_text=jd_text,
        include_constraints=True
    )
    
    # Perform evaluation
    print("\n🔍 Evaluating CV against Job Description using Groq...")
    try:
        result = engine.evaluate(request)
        
        # Display results
        print(f"\n📊 EVALUATION RESULTS")
        print("=" * 50)
        print(f"🎯 Overall Fit Index: {result.fit_index}/100 ({result.band})")
        print(f"📋 CV Quality: {result.cv_quality.overall_score}/100 ({result.cv_quality.band})")
        print(f"🎯 JD Match: {result.jd_match.overall_score}/100 ({result.jd_match.band})")
        
        print(f"\n📋 CV QUALITY DETAILS:")
        for subscore in result.cv_quality.subscores:
            print(f"  • {subscore.dimension}: {subscore.score}/{subscore.max_score}")
            if subscore.evidence:
                print(f"    Evidence: {subscore.evidence[0][:80]}...")
        
        print(f"\n🎯 JD MATCH DETAILS:")
        for subscore in result.jd_match.subscores:
            print(f"  • {subscore.dimension}: {subscore.score}/{subscore.max_score}")
            if subscore.evidence:
                print(f"    Evidence: {subscore.evidence[0][:80]}...")
        
        print(f"\n🔒 CONSTRAINTS: {result.constraints_disclosure.constraints_score}/10")
        if result.constraints_disclosure.constraints_evidence:
            print("Evidence:")
            for evidence in result.constraints_disclosure.constraints_evidence:
                print(f"  • {evidence}")
        
        print("\n✅ Evaluation completed successfully using Groq!")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        print("   Falling back to heuristic scoring...")
        
        # Fallback to heuristic
        engine_fallback = CVEvaluationEngine(use_llm=False)
        result = engine_fallback.evaluate(request)
        print(f"   Fallback result: {result.fit_index}/100 ({result.band})")


if __name__ == "__main__":
    example_groq_usage()
