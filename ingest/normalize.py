import re
from typing import Dict, List, Any, Optional
from datetime import datetime


def normalize_cv(text: str) -> Dict[str, Any]:
    """Normalize CV text into structured data"""
    normalized = {
        "personal_info": extract_personal_info(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "skills": extract_skills(text),
        "projects": extract_projects(text),
        "certifications": extract_certifications(text),
        "languages": extract_languages(text)
    }
    
    return normalized


def normalize_jd(text: str) -> Dict[str, Any]:
    """Normalize job description text into structured data"""
    normalized = {
        "job_title": extract_job_title(text),
        "company_info": extract_company_info(text),
        "requirements": extract_requirements(text),
        "responsibilities": extract_responsibilities(text),
        "qualifications": extract_qualifications(text),
        "benefits": extract_benefits(text),
        "location": extract_location(text),
        "employment_type": extract_employment_type(text)
    }
    
    return normalized


def extract_personal_info(text: str) -> Dict[str, str]:
    """Extract personal information from CV"""
    info = {}
    
    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        info["email"] = email_match.group()
    
    # Phone
    phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        info["phone"] = ''.join(phone_match.groups())
    
    # Name (simple heuristic - first line that's not empty)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        info["name"] = lines[0]
    
    return info


def extract_education(text: str) -> List[Dict[str, str]]:
    """Extract education information from CV"""
    education = []
    
    # Look for education section
    education_patterns = [
        r'education',
        r'educational background',
        r'academic background',
        r'qualifications'
    ]
    
    for pattern in education_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract lines after education section
            lines = text.split('\n')
            in_education = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_education = True
                    continue
                
                if in_education and line:
                    # Simple parsing - look for degree patterns
                    degree_patterns = [
                        r'bachelor',
                        r'master',
                        r'phd',
                        r'doctorate',
                        r'diploma',
                        r'certificate'
                    ]
                    
                    if any(re.search(deg, line, re.IGNORECASE) for deg in degree_patterns):
                        education.append({
                            "degree": line,
                            "institution": "",  # Would need more sophisticated parsing
                            "year": ""
                        })
            
            break
    
    return education


def extract_experience(text: str) -> List[Dict[str, str]]:
    """Extract work experience from CV"""
    experience = []
    
    # Look for experience section
    experience_patterns = [
        r'experience',
        r'work history',
        r'employment history',
        r'professional background'
    ]
    
    for pattern in experience_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract lines after experience section
            lines = text.split('\n')
            in_experience = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_experience = True
                    continue
                
                if in_experience and line:
                    # Look for job title patterns
                    job_patterns = [
                        r'engineer',
                        r'developer',
                        r'manager',
                        r'analyst',
                        r'consultant',
                        r'lead',
                        r'architect'
                    ]
                    
                    if any(re.search(job, line, re.IGNORECASE) for job in job_patterns):
                        experience.append({
                            "title": line,
                            "company": "",
                            "duration": "",
                            "description": ""
                        })
            
            break
    
    return experience


def extract_skills(text: str) -> List[str]:
    """Extract skills from CV"""
    skills = []
    
    # Look for skills section
    skills_patterns = [
        r'skills',
        r'technical skills',
        r'competencies',
        r'expertise'
    ]
    
    for pattern in skills_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract skills after the section header
            lines = text.split('\n')
            in_skills = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_skills = True
                    continue
                
                if in_skills and line:
                    # Split by common delimiters
                    skill_items = re.split(r'[,;|•]', line)
                    for skill in skill_items:
                        skill = skill.strip()
                        if skill and len(skill) > 2:
                            skills.append(skill)
            
            break
    
    return skills


def extract_projects(text: str) -> List[Dict[str, str]]:
    """Extract projects from CV"""
    projects = []
    
    # Look for projects section
    project_patterns = [
        r'projects',
        r'portfolio',
        r'achievements'
    ]
    
    for pattern in project_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # Extract project information
            lines = text.split('\n')
            in_projects = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_projects = True
                    continue
                
                if in_projects and line:
                    if len(line) > 20:  # Likely a project description
                        projects.append({
                            "title": line[:50] + "..." if len(line) > 50 else line,
                            "description": line
                        })
            
            break
    
    return projects


def extract_certifications(text: str) -> List[str]:
    """Extract certifications from CV"""
    certifications = []
    
    # Look for certification patterns
    cert_patterns = [
        r'certified',
        r'certification',
        r'license'
    ]
    
    for pattern in cert_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extract surrounding context
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            certifications.append(context.strip())
    
    return certifications


def extract_languages(text: str) -> List[str]:
    """Extract languages from CV"""
    languages = []
    
    # Common language patterns
    language_patterns = [
        r'english',
        r'spanish',
        r'french',
        r'german',
        r'chinese',
        r'japanese',
        r'korean',
        r'arabic',
        r'portuguese',
        r'italian'
    ]
    
    for pattern in language_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            languages.append(pattern.capitalize())
    
    return languages


def extract_job_title(text: str) -> str:
    """Extract job title from JD"""
    # Look for common job title patterns
    title_patterns = [
        r'position:\s*(.+)',
        r'job title:\s*(.+)',
        r'role:\s*(.+)',
        r'we are looking for a (.+)',
        r'seeking a (.+)'
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""


def extract_company_info(text: str) -> Dict[str, str]:
    """Extract company information from JD"""
    info = {}
    
    # Company name
    company_patterns = [
        r'about (.+)',
        r'at (.+)',
        r'join (.+)'
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["name"] = match.group(1).strip()
            break
    
    return info


def extract_requirements(text: str) -> List[str]:
    """Extract job requirements from JD"""
    requirements = []
    
    # Look for requirements section
    req_patterns = [
        r'requirements',
        r'qualifications',
        r'what you need',
        r'what we require'
    ]
    
    for pattern in req_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            lines = text.split('\n')
            in_requirements = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_requirements = True
                    continue
                
                if in_requirements and line:
                    if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                        requirements.append(line[1:].strip())
                    elif len(line) > 10:
                        requirements.append(line)
            
            break
    
    return requirements


def extract_responsibilities(text: str) -> List[str]:
    """Extract job responsibilities from JD"""
    responsibilities = []
    
    # Look for responsibilities section
    resp_patterns = [
        r'responsibilities',
        r'what you will do',
        r'key duties',
        r'role and responsibilities'
    ]
    
    for pattern in resp_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            lines = text.split('\n')
            in_responsibilities = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_responsibilities = True
                    continue
                
                if in_responsibilities and line:
                    if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                        responsibilities.append(line[1:].strip())
                    elif len(line) > 10:
                        responsibilities.append(line)
            
            break
    
    return responsibilities


def extract_qualifications(text: str) -> List[str]:
    """Extract qualifications from JD"""
    qualifications = []
    
    # Look for qualifications section
    qual_patterns = [
        r'qualifications',
        r'education',
        r'experience level',
        r'background'
    ]
    
    for pattern in qual_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            lines = text.split('\n')
            in_qualifications = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_qualifications = True
                    continue
                
                if in_qualifications and line:
                    if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                        qualifications.append(line[1:].strip())
                    elif len(line) > 10:
                        qualifications.append(line)
            
            break
    
    return qualifications


def extract_benefits(text: str) -> List[str]:
    """Extract benefits from JD"""
    benefits = []
    
    # Look for benefits section
    benefit_patterns = [
        r'benefits',
        r'perks',
        r'what we offer',
        r'compensation'
    ]
    
    for pattern in benefit_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            lines = text.split('\n')
            in_benefits = False
            
            for line in lines:
                line = line.strip()
                if re.search(pattern, line, re.IGNORECASE):
                    in_benefits = True
                    continue
                
                if in_benefits and line:
                    if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                        benefits.append(line[1:].strip())
                    elif len(line) > 10:
                        benefits.append(line)
            
            break
    
    return benefits


def extract_location(text: str) -> str:
    """Extract job location from JD"""
    # Look for location patterns
    location_patterns = [
        r'location:\s*(.+)',
        r'based in (.+)',
        r'remote',
        r'hybrid',
        r'on-site'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip() if len(match.groups()) > 0 else pattern
    
    return ""


def extract_employment_type(text: str) -> str:
    """Extract employment type from JD"""
    # Look for employment type patterns
    type_patterns = [
        r'full-time',
        r'part-time',
        r'contract',
        r'internship',
        r'freelance'
    ]
    
    for pattern in type_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return pattern
    
    return "full-time"  # Default assumption
