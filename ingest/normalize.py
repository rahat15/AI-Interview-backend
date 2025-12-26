"""Mock normalization module"""

def normalize_cv(text: str) -> dict:
    """Normalize CV text - mock implementation"""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "FastAPI", "MongoDB"],
        "experience": "5 years",
        "education": "Computer Science"
    }

def normalize_jd(text: str) -> dict:
    """Normalize JD text - mock implementation"""
    return {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "requirements": ["Python", "API Development", "Database"],
        "experience_required": "3-5 years",
        "location": "Remote"
    }