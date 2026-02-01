#!/usr/bin/env python3
"""
Test script for the resume optimization endpoint
"""

import requests
import json

# Sample data from your example
sample_data = {
    "message": "Resume uploaded successfully",
    "resume": {
        "id": "697f8b7595bf1a57ebf3440c",
        "filename": "Akash_Resume .pdf",
        "url": "http://localhost:3000/uploads/users/6968966ba463d2d4480cbe48/1769966450892-Akash_Resume .pdf",
        "analytics": {
            "cv_quality": {
                "overall_score": 82,
                "subscores": [
                    {
                        "dimension": "ats_structure",
                        "score": 8,
                        "max_score": 10,
                        "evidence": [
                            "+91 7617644460 | akashkum71@gmail.com | linkedin.com/in/akash-bargoti | github.com/AkashKumar2000"
                        ]
                    },
                    {
                        "dimension": "writing_clarity",
                        "score": 12,
                        "max_score": 15,
                        "evidence": [
                            "• Built an AI-powered document summarization platform supporting PDF, DOCX, and TXT files.",
                            "• Developed a real-time chat application using Socket.IO for live communication."
                        ]
                    },
                    {
                        "dimension": "quantified_impact",
                        "score": 16,
                        "max_score": 20,
                        "evidence": [
                            "• Achieved an 18% improvement in Sharpe Ratio over traditional MPT models."
                        ]
                    },
                    {
                        "dimension": "technical_depth",
                        "score": 12,
                        "max_score": 15,
                        "evidence": [
                            "FastAPI, NLP, Transformers",
                            "MongoDB, Express, React, Node.js",
                            "Python, LSTM, Machine Learning"
                        ]
                    },
                    {
                        "dimension": "projects_portfolio",
                        "score": 8,
                        "max_score": 10,
                        "evidence": [
                            "AI Document Summarizer",
                            "Real-Time MERN Chat Application",
                            "LSTM-Based Portfolio Optimization"
                        ]
                    },
                    {
                        "dimension": "leadership_skills",
                        "score": 6,
                        "max_score": 10,
                        "evidence": [
                            "Software Engineering Intern EPAM Systems"
                        ]
                    },
                    {
                        "dimension": "career_progression",
                        "score": 8,
                        "max_score": 10,
                        "evidence": [
                            "M.E. in Artificial Intelligence Aug. 2025 – Present",
                            "B.Tech in Computer Science & Engineering - CGPA: 7.25 Aug. 2019 – May 2023"
                        ]
                    },
                    {
                        "dimension": "consistency",
                        "score": 8,
                        "max_score": 10,
                        "evidence": [
                            "Formatting, tone, and verb tenses are consistent throughout the document."
                        ]
                    }
                ]
            },
            "jd_match": {
                "overall_score": 62,
                "subscores": [
                    {
                        "dimension": "hard_skills",
                        "score": 24,
                        "max_score": 35,
                        "evidence": [
                            "Strong knowledge of JavaScript / TypeScript",
                            "Experience with React or similar frontend frameworks",
                            "Experience with Node.js / NestJS backend development",
                            "Knowledge of REST APIs and databases"
                        ]
                    },
                    {
                        "dimension": "responsibilities",
                        "score": 10,
                        "max_score": 15,
                        "evidence": [
                            "Develop and maintain web applications and dashboards",
                            "Build scalable backend APIs and services"
                        ]
                    },
                    {
                        "dimension": "domain_relevance",
                        "score": 6,
                        "max_score": 10,
                        "evidence": [
                            "Interactive digital solutions, including 3D menus, smart restaurant systems, and modern web applications for the hospitality industry."
                        ]
                    },
                    {
                        "dimension": "seniority",
                        "score": 6,
                        "max_score": 10,
                        "evidence": [
                            "M.E. in Artificial Intelligence Aug. 2025 – Present"
                        ]
                    },
                    {
                        "dimension": "nice_to_haves",
                        "score": 2,
                        "max_score": 5,
                        "evidence": [
                            "Experience with cloud platforms and VPS deployments"
                        ]
                    },
                    {
                        "dimension": "education_certs",
                        "score": 0,
                        "max_score": 5,
                        "evidence": [
                            "No evidence found."
                        ]
                    },
                    {
                        "dimension": "recent_achievements",
                        "score": 6,
                        "max_score": 10,
                        "evidence": [
                            "• Achieved an 18% improvement in Sharpe Ratio over traditional MPT models."
                        ]
                    },
                    {
                        "dimension": "constraints",
                        "score": 8,
                        "max_score": 10,
                        "evidence": [
                            "Hybrid / Remote (India)"
                        ]
                    }
                ]
            },
            "key_takeaways": {
                "red_flags": [
                    "No direct experience with 3D, WebGL, or interactive UI concepts.",
                    "No experience with Electron or mobile development."
                ],
                "green_flags": [
                    "Strong knowledge of JavaScript / TypeScript and experience with React or similar frontend frameworks.",
                    "Experience with Node.js / NestJS backend development and knowledge of REST APIs and databases.",
                    "Achieved an 18% improvement in Sharpe Ratio over traditional MPT models."
                ]
            },
            "overall_score": 82
        },
        "enhancement": {
            "tailored_resume": {
                "summary": "Highly motivated Software Developer with expertise in building scalable web applications, interactive user experiences, and backend services using modern frontend frameworks, Node.js, and REST APIs. Proficient in JavaScript, TypeScript, React, and Node.js, with a strong passion for innovative 3D-based products and collaborative team culture.",
                "experience": [
                    "Developed and maintained web applications and dashboards using React and Node.js, with a focus on scalability and performance.",
                    "Built scalable backend APIs and services using Node.js and REST APIs, with a strong emphasis on security and data integrity."
                ],
                "skills": [
                    "JavaScript",
                    "TypeScript",
                    "React",
                    "Node.js",
                    "REST APIs",
                    "MongoDB",
                    "Git"
                ],
                "projects": [
                    "AI Document Summarizer: Built an AI-powered document summarization platform using FastAPI, NLP, and Transformers, with a focus on scalability and performance.",
                    "Real-Time MERN Chat Application: Developed a real-time chat application using Socket.IO, MongoDB, and Node.js, with a strong emphasis on security and data integrity."
                ]
            },
            "top_1_percent_gap": {
                "strengths": [
                    "Strong knowledge of JavaScript, TypeScript, and React",
                    "Experience with Node.js and REST APIs"
                ],
                "gaps": [
                    "Lack of experience with cloud platforms and VPS deployments",
                    "Limited understanding of 3D, WebGL, or interactive UI concepts"
                ],
                "actionable_next_steps": [
                    "Take online courses or attend workshops to learn about cloud platforms and VPS deployments",
                    "Explore and learn about 3D, WebGL, or interactive UI concepts through online resources or personal projects"
                ]
            },
            "cover_letter": "Dear Hiring Manager, I am excited to apply for the Software Developer position at Dine3D. With my strong background in building scalable web applications, interactive user experiences, and backend services using modern frontend frameworks, Node.js, and REST APIs, I am confident that I can make a valuable contribution to your team. I am particularly drawn to Dine3D's innovative 3D-based products and collaborative team culture. I look forward to discussing my application and how I can contribute to your success. Thank you for considering my application."
        }
    }
}

def test_resume_optimization():
    """Test the resume optimization endpoint"""
    url = "http://localhost:8000/v1/resume/optimize"
    
    try:
        print("🧪 Testing resume optimization endpoint...")
        print(f"📍 URL: {url}")
        
        response = requests.post(
            url,
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Optimized CV content:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_resume_optimization()