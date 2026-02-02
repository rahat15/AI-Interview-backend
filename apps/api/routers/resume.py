from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import uuid
import aiofiles
from datetime import datetime
import json
import re
import google.generativeai as genai

from core.models import Resume
from core.config import settings
from core.schemas import ResumeAnalysisRequest, CVOptimizationResponse, OptimizedCVContent, ResumeBuilderResponse, ResumeBuilderContent
from ingest.extract import extract_text_from_file
from apps.api.eval_engine_instance import evaluation_engine
from cv_eval.improvement import Improvement

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)

router = APIRouter()

improvement_engine = Improvement()

async def save_resume_file(file: UploadFile, user_id: str = "default") -> str:
    """Save resume file to server and return file path"""
    upload_dir = os.path.join(settings.upload_dir, "users", user_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{int(datetime.now().timestamp() * 1000)}-{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return f"uploads/users/{user_id}/{unique_filename}"

@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form("default"),
    jd_text: Optional[str] = Form(None)
):
    """
    Upload resume and get comprehensive analysis including:
    - CV quality scores
    - Strengths and weaknesses
    - ATS compatibility
    - Keyword analysis
    - Improvement suggestions
    - Rewritten sections
    """
    try:
        # Save file
        file_path = await save_resume_file(file, user_id)
        full_path = os.path.join(settings.upload_dir, "..", file_path)
        
        # Extract text
        cv_text = await extract_text_from_file(full_path)
        
        # LOG: Print extracted text for debugging
        print("=" * 80)
        print("📄 EXTRACTED PDF TEXT:")
        print("=" * 80)
        print(cv_text[:1000] if len(cv_text) > 1000 else cv_text)  # First 1000 chars
        print(f"\n... (Total length: {len(cv_text)} characters)")
        print("=" * 80)
        
        # Evaluate CV quality
        cv_evaluation = evaluation_engine.evaluate(cv_text, jd_text or "")
        
        # Get improvement suggestions if JD provided
        improvement_data = None
        if jd_text and jd_text.strip():
            try:
                improvement_data = improvement_engine.evaluate(cv_text, jd_text)
            except Exception as e:
                # Log error but don't fail the request
                import logging
                logging.error(f"Improvement generation failed: {e}")
                improvement_data = None
        
        # Create resume document in MongoDB
        resume_doc = Resume(
            filename=file.filename,
            path=file_path,
            user=user_id,
            stats={
                "cv_quality": cv_evaluation.get("cv_quality", {}),
                "jd_match": cv_evaluation.get("jd_match", {}),
                "fit_index": cv_evaluation.get("fit_index", {})
            }
        )
        
        await resume_doc.insert()
        
        # Build comprehensive response
        cv_quality = cv_evaluation.get("cv_quality", {})
        subscores = cv_quality.get("subscores", [])
        key_takeaways = cv_evaluation.get("key_takeaways", {})
        
        # Extract strengths and weaknesses from key_takeaways
        strengths = key_takeaways.get("green_flags", [])
        weaknesses = key_takeaways.get("red_flags", [])
        
        # Fallback to subscores if no key_takeaways
        if not strengths:
            for subscore in subscores:
                evidence = subscore.get("evidence", [])
                score = subscore.get("score", 0)
                max_score = subscore.get("max_score", 10)
                if score >= max_score * 0.8:
                    strengths.extend(evidence[:1])
        
        if not weaknesses:
            for subscore in subscores:
                evidence = subscore.get("evidence", [])
                score = subscore.get("score", 0)
                max_score = subscore.get("max_score", 10)
                if score < max_score * 0.5:
                    weaknesses.extend(evidence[:1])
        
        # Build response matching expected format
        response = {
            "message": "Resume uploaded successfully",
            "resume": {
                "id": str(resume_doc.id),
                "filename": file.filename,
                "url": f"http://localhost:3000/{file_path}",
                "stats": {
                    "overall_score": round(cv_quality.get("overall_score", 0) / 10, 1),
                    "sections": {},
                    "strengths": strengths[:4] if strengths else ["Professional formatting", "Clear structure"],
                    "weaknesses": weaknesses[:3] if weaknesses else ["Could add more details"],
                    "recommendations": [
                        "Add quantifiable achievements",
                        "Include relevant keywords",
                        "Optimize for ATS compatibility"
                    ],
                    "ats_compatibility": {
                        "score": 8.5,
                        "issues": ["Use standard section headings", "Avoid complex formatting"]
                    },
                    "keyword_analysis": {
                        "matched_keywords": [],
                        "missing_keywords": [],
                        "keyword_density": 0.12
                    }
                }
            }
        }
        
        # Add sections scores
        for subscore in subscores:
            section_name = subscore.get("dimension", "").lower().replace(" ", "_")
            response["resume"]["stats"]["sections"][section_name] = {
                "score": round(subscore.get("score", 0), 1),
                "feedback": ", ".join(subscore.get("evidence", [])[:2])
            }
        
        # Add improvement data if available
        if improvement_data:
            tailored = improvement_data.get("tailored_resume", {})
            gap_analysis = improvement_data.get("top_1_percent_gap", {})
            
            response["resume"]["improvement_resume"] = {
                "tailored_resume": tailored,
                "top_1_percent_benchmark": {
                    "strengths": gap_analysis.get("strengths", []),
                    "gaps": gap_analysis.get("gaps", []),
                    "actionable_next_steps": gap_analysis.get("actionable_next_steps", [])
                },
                "cover_letter": improvement_data.get("cover_letter", "")
            }
        else:
            # Don't include improvement_resume if no JD provided or if generation failed
            response["resume"]["improvement_resume"] = None
        
        # Add raw evaluation data
        response["cv_quality"] = cv_quality
        response["jd_match"] = cv_evaluation.get("jd_match", {})
        response["fit_index"] = cv_evaluation.get("fit_index", {})
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/resume/optimize", response_model=CVOptimizationResponse)
async def optimize_resume_content(request: ResumeAnalysisRequest):
    """
    Generate optimized CV content from resume analysis data.
    Takes the JSON response from resume upload and returns the best CV content
    for resume preparation including tailored sections, keywords, and improvements.
    """
    try:
        resume_data = request.resume
        analytics = resume_data.analytics
        enhancement = resume_data.enhancement
        
        # Extract key information
        cv_quality = analytics.cv_quality
        jd_match = analytics.jd_match
        key_takeaways = analytics.key_takeaways
        tailored_resume = enhancement.tailored_resume
        gap_analysis = enhancement.top_1_percent_gap
        
        # Calculate confidence score based on overall scores
        confidence_score = min(95.0, (cv_quality.overall_score + jd_match.overall_score) / 2.0)
        
        # Extract ATS keywords from evidence
        ats_keywords = []
        for subscore in cv_quality.subscores:
            if subscore.dimension == "ats_structure":
                for evidence in subscore.evidence:
                    # Extract potential keywords from evidence
                    words = evidence.replace("|", " ").replace(",", " ").split()
                    ats_keywords.extend([word.strip() for word in words if len(word) > 2])
        
        # Get technical skills from evidence
        technical_skills = []
        for subscore in cv_quality.subscores:
            if subscore.dimension == "technical_depth":
                technical_skills.extend(subscore.evidence)
        
        # Combine with tailored skills
        all_skills = list(set(tailored_resume.skills + technical_skills))
        
        # Extract achievements from quantified impact
        achievements = []
        for subscore in cv_quality.subscores:
            if subscore.dimension == "quantified_impact":
                achievements.extend(subscore.evidence)
        
        # Get project highlights
        project_descriptions = tailored_resume.projects
        
        # Create improvement priority based on gaps
        improvement_priority = gap_analysis.actionable_next_steps
        
        # Generate recommendations based on red flags and gaps
        recommendations = []
        for red_flag in key_takeaways.red_flags[:3]:
            recommendations.append(f"Address: {red_flag}")
        
        for gap in gap_analysis.gaps[:2]:
            recommendations.append(f"Improve: {gap}")
        
        # Build optimized content
        optimized_content = OptimizedCVContent(
            professional_summary=tailored_resume.summary,
            key_skills=all_skills[:10],  # Top 10 skills
            experience_highlights=tailored_resume.experience,
            project_descriptions=project_descriptions,
            achievements=achievements,
            recommendations=recommendations,
            cover_letter_template=enhancement.cover_letter,
            ats_keywords=list(set(ats_keywords))[:15],  # Top 15 unique keywords
            improvement_priority=improvement_priority
        )
        
        return CVOptimizationResponse(
            status="success",
            optimized_content=optimized_content,
            confidence_score=confidence_score,
            message="CV content optimized successfully based on analysis data"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"CV optimization failed: {str(e)}"
        )


@router.post("/resume/generate", response_model=ResumeBuilderResponse)
async def generate_resume_content(request: ResumeAnalysisRequest):
    """
    Generate complete resume JSON content that can be used to build a professional resume.
    Returns structured data including personal info, experience, projects, skills, etc.
    """
    try:
        resume_data = request.resume
        analytics = resume_data.analytics
        enhancement = resume_data.enhancement
        
        # Extract information
        cv_quality = analytics.cv_quality
        tailored_resume = enhancement.tailored_resume
        gap_analysis = enhancement.top_1_percent_gap
        
        # Extract contact info from ATS structure evidence
        contact_info = {}
        for subscore in cv_quality.subscores:
            if subscore.dimension == "ats_structure" and subscore.evidence:
                contact_text = subscore.evidence[0]
                if "|" in contact_text:
                    parts = contact_text.split("|")
                    for part in parts:
                        part = part.strip()
                        if "@" in part:
                            contact_info["email"] = part
                        elif part.startswith("+") or part.replace("-", "").replace(" ", "").isdigit():
                            contact_info["phone"] = part
                        elif "linkedin.com" in part:
                            contact_info["linkedin"] = part
                        elif "github.com" in part:
                            contact_info["github"] = part
        
        # Default contact info if not found
        personal_info = {
            "name": "Your Name",
            "email": contact_info.get("email", "your.email@example.com"),
            "phone": contact_info.get("phone", "+1 (555) 123-4567"),
            "location": "City, State",
            "linkedin": contact_info.get("linkedin", "linkedin.com/in/yourprofile"),
            "github": contact_info.get("github", "github.com/yourusername"),
            "website": "yourwebsite.com"
        }
        
        # Skills categorization
        technical_skills = []
        soft_skills = []
        tools_frameworks = []
        
        for skill in tailored_resume.skills:
            if any(tech in skill.lower() for tech in ["javascript", "python", "java", "react", "node", "api", "database", "sql"]):
                technical_skills.append(skill)
            elif any(tool in skill.lower() for tech in ["git", "docker", "aws", "mongodb", "express"]):
                tools_frameworks.append(skill)
            else:
                soft_skills.append(skill)
        
        skills = {
            "technical": technical_skills[:8],
            "frameworks_tools": tools_frameworks[:6],
            "soft_skills": soft_skills[:4] if soft_skills else ["Problem Solving", "Team Collaboration", "Communication", "Leadership"]
        }
        
        # Experience from tailored resume
        experience = []
        for i, exp in enumerate(tailored_resume.experience):
            experience.append({
                "title": "Software Developer" if i == 0 else "Junior Developer",
                "company": "Company Name",
                "location": "City, State",
                "duration": "Jan 2023 - Present" if i == 0 else "Jun 2022 - Dec 2022",
                "description": [exp],
                "technologies": technical_skills[:3]
            })
        
        # Projects from tailored resume
        projects = []
        for project_desc in tailored_resume.projects:
            project_name = project_desc.split(":")[0] if ": " in project_desc else f"Project {len(projects) + 1}"
            description = project_desc.split(": ", 1)[1] if ": " in project_desc else project_desc
            
            projects.append({
                "name": project_name,
                "description": description,
                "technologies": technical_skills[:4],
                "github": "https://github.com/yourusername/project-name",
                "demo": "https://your-project-demo.com",
                "highlights": [
                    "Implemented key features",
                    "Optimized performance",
                    "Deployed to production"
                ]
            })
        
        # Education from career progression evidence
        education = []
        for subscore in cv_quality.subscores:
            if subscore.dimension == "career_progression":
                for evidence in subscore.evidence:
                    if "M.E." in evidence or "B.Tech" in evidence:
                        parts = evidence.split()
                        degree = " ".join(parts[:2]) if len(parts) >= 2 else "Degree"
                        field = " ".join(parts[3:7]) if len(parts) > 7 else "Computer Science"
                        duration = " ".join(parts[-4:]) if len(parts) >= 4 else "2019 - 2023"
                        
                        education.append({
                            "degree": degree,
                            "field": field,
                            "institution": "University Name",
                            "duration": duration,
                            "gpa": "7.25" if "CGPA: 7.25" in evidence else "3.5"
                        })
        
        # Default education if none found
        if not education:
            education = [{
                "degree": "Bachelor of Technology",
                "field": "Computer Science & Engineering",
                "institution": "University Name",
                "duration": "2019 - 2023",
                "gpa": "3.5"
            }]
        
        # Achievements from quantified impact
        achievements = []
        for subscore in cv_quality.subscores:
            if subscore.dimension == "quantified_impact":
                achievements.extend(subscore.evidence)
        
        # Default achievements if none found
        if not achievements:
            achievements = [
                "Improved system performance by 20%",
                "Led team of 3 developers on key project",
                "Reduced code deployment time by 30%"
            ]
        
        # Certifications and languages
        certifications = [
            {"name": "AWS Certified Developer", "issuer": "Amazon Web Services", "date": "2023"},
            {"name": "React Developer Certification", "issuer": "Meta", "date": "2023"}
        ]
        
        languages = [
            {"language": "English", "proficiency": "Native"},
            {"language": "Hindi", "proficiency": "Fluent"}
        ]
        
        # Build resume content
        resume_content = ResumeBuilderContent(
            personal_info=personal_info,
            professional_summary=tailored_resume.summary,
            skills=skills,
            experience=experience,
            projects=projects,
            education=education,
            achievements=achievements,
            certifications=certifications,
            languages=languages
        )
        
        # Formatting tips
        formatting_tips = [
            "Use a clean, professional font like Arial or Calibri",
            "Keep resume to 1-2 pages maximum",
            "Use bullet points for easy readability",
            "Include quantifiable achievements with numbers",
            "Tailor keywords to match job descriptions",
            "Use consistent formatting throughout",
            "Save as PDF to preserve formatting",
            "Include relevant technical skills prominently"
        ]
        
        return ResumeBuilderResponse(
            status="success",
            resume_content=resume_content,
            formatting_tips=formatting_tips,
            message="Complete resume content generated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume generation failed: {str(e)}"
        )


@router.post("/resume/final-enhanced", response_model=ResumeBuilderResponse)
async def generate_final_enhanced_resume(request: ResumeAnalysisRequest):
    """
    AI-enhanced resume generator using Google Gemini 2.5 Pro.
    Generates professional, ATS-optimized resume content with intelligent data extraction.
    """
    try:
        # Support both nested (resume field) and direct field structure
        if request.resume:
            resume_data = request.resume
        else:
            # Create ResumeData from direct fields
            from core.schemas import ResumeData
            resume_data = ResumeData(
                id=request.id,
                filename=request.filename,
                url=request.url,
                analytics=request.analytics,
                enhancement=request.enhancement
            )
        
        analytics = resume_data.analytics
        enhancement = resume_data.enhancement
        
        # Prepare comprehensive context for Gemini
        context_data = {
            "cv_quality": {
                "overall_score": analytics.cv_quality.overall_score,
                "subscores": [
                    {
                        "dimension": sub.dimension,
                        "score": sub.score,
                        "max_score": sub.max_score,
                        "evidence": sub.evidence
                    }
                    for sub in analytics.cv_quality.subscores
                ]
            },
            "jd_match": {
                "overall_score": analytics.jd_match.overall_score if analytics.jd_match else 0,
                "subscores": [
                    {
                        "dimension": sub.dimension,
                        "score": sub.score,
                        "max_score": sub.max_score,
                        "evidence": sub.evidence
                    }
                    for sub in (analytics.jd_match.subscores if analytics.jd_match else [])
                ]
            },
            "key_takeaways": {
                "green_flags": analytics.key_takeaways.green_flags,
                "red_flags": analytics.key_takeaways.red_flags
            },
            "tailored_resume": {
                "summary": enhancement.tailored_resume.summary,
                "skills": enhancement.tailored_resume.skills,
                "experience": enhancement.tailored_resume.experience,
                "projects": enhancement.tailored_resume.projects
            },
            "top_1_percent_gap": {
                "strengths": enhancement.top_1_percent_gap.strengths,
                "gaps": enhancement.top_1_percent_gap.gaps,
                "actionable_next_steps": enhancement.top_1_percent_gap.actionable_next_steps
            }
        }
        
        # LOG: Print context data being sent to Gemini
        print("\n" + "=" * 80)
        print("🔍 CONTEXT DATA SENT TO GEMINI:")
        print("=" * 80)
        print(f"\n📊 CV Quality Score: {context_data['cv_quality']['overall_score']}")
        print(f"\n📝 Number of Subscores: {len(context_data['cv_quality']['subscores'])}")
        
        # Log each subscore with evidence
        for subscore in context_data['cv_quality']['subscores']:
            print(f"\n🔹 {subscore['dimension'].upper()}: {subscore['score']}/{subscore['max_score']}")
            print(f"   Evidence ({len(subscore['evidence'])} items):")
            for i, evidence_item in enumerate(subscore['evidence'][:3]):  # Show first 3
                print(f"   [{i+1}] {evidence_item[:200]}...")  # First 200 chars
        
        print(f"\n✅ Green Flags: {context_data['key_takeaways']['green_flags']}")
        print(f"⚠️  Red Flags: {context_data['key_takeaways']['red_flags']}")
        
        print(f"\n📋 Tailored Resume Summary: {context_data['tailored_resume']['summary'][:200]}...")
        print(f"💡 Skills ({len(context_data['tailored_resume']['skills'])}): {context_data['tailored_resume']['skills'][:10]}")
        print(f"💼 Experience ({len(context_data['tailored_resume']['experience'])} items)")
        print(f"🚀 Projects ({len(context_data['tailored_resume']['projects'])} items)")
        print("=" * 80 + "\n")
        
        # Create Gemini prompt for resume enhancement
        prompt = f"""You are an expert resume writer and career coach. Based on the comprehensive resume analysis data provided, generate the best possible professional resume content.

ANALYSIS DATA:
{json.dumps(context_data, indent=2)}

YOUR TASK:
Generate a complete, professional resume in JSON format with the following structure. Extract and enhance all information intelligently from the evidence and data provided.

CRITICAL EXTRACTION RULES:
1. **Personal Information** - SEARCH THOROUGHLY in ALL evidence fields for:
   - Name: Look for patterns like "Name:", names at start of evidence, or in ATS structure
   - Email: Search for @domain patterns in ALL subscores evidence
   - Phone: Search for phone number patterns (+91, +1, etc.) in ALL evidence
   - LinkedIn: Search for "linkedin.com/in/" URLs in ALL evidence
   - GitHub: Search for "github.com/" URLs in ALL evidence
   - Location: Search for city names, state names, "India", country names in evidence

2. **Professional Summary**: 
   - Extract the EXACT summary from tailored_resume.summary
   - Enhance it slightly if needed, but keep core content
   - Highlight quantified achievements mentioned in evidence

3. **Skills**: 
   - Extract ALL skills from tailored_resume.skills
   - Add any additional skills found in technical_depth evidence
   - Categorize intelligently: technical (languages/frameworks), tools (platforms/software), soft skills

4. **Experience**: 
   - Extract work history details from evidence (leadership_skills, career_progression dimensions)
   - Look for company names, job titles, dates in the evidence
   - Extract responsibilities from tailored_resume.experience
   - Add quantified metrics from quantified_impact dimension
   - Use strong action verbs: developed, architected, led, optimized, delivered, etc.

5. **Projects**: 
   - Extract from tailored_resume.projects
   - Look for project names (often before colons)
   - Include download numbers, user metrics from quantified_impact evidence
   - Extract technologies mentioned in project descriptions

6. **Education**: 
   - Search career_progression evidence for degree patterns (B.Tech, M.E., Bachelor, Master, etc.)
   - Extract institution names (look for University, Institute, College)
   - Extract CGPA/GPA if mentioned
   - Extract duration/years

7. **Achievements**: 
   - Extract ALL items from quantified_impact evidence
   - These should contain actual numbers and metrics
   - Keep the exact wording but make them concise

8. **Certifications**: 
   - Infer based on skills (JavaScript → relevant certs)
   - Only add 1-2 most relevant certifications
   - Make them realistic for the skill set

IMPORTANT: 
- If you find REAL data in evidence (email, phone, name), USE IT - don't use defaults
- Look in ALL subscore evidence arrays, not just the first one
- Preserve numbers and metrics exactly as found in evidence
- If truly no data found for a field, then use professional defaults

OUTPUT FORMAT (valid JSON only):
{{
  "personal_info": {{
    "name": "EXTRACT FROM EVIDENCE or use first name from email or 'Professional Developer'",
    "email": "EXTRACT FROM EVIDENCE (search for @ symbol) or 'your.email@example.com'",
    "phone": "EXTRACT FROM EVIDENCE (search for phone patterns) or '+91 XXX XXX XXXX'",
    "location": "EXTRACT FROM EVIDENCE (search for India, city names) or 'India'",
    "linkedin": "EXTRACT FROM EVIDENCE (search for linkedin.com) or ''",
    "github": "EXTRACT FROM EVIDENCE (search for github.com) or ''",
    "website": ""
  }},
  "professional_summary": "Use tailored_resume.summary, enhance with key achievements",
  "skills": {{
    "technical": ["from tailored_resume.skills + technical_depth evidence"],
    "tools": ["platforms, frameworks, tools from skills"],
    "soft_skills": ["leadership, communication, problem-solving"]
  }},
  "experience": [
    {{
      "title": "EXTRACT from evidence or tailored experience",
      "company": "EXTRACT from evidence or 'Technology Company'",
      "location": "EXTRACT or 'India' or 'Remote'",
      "duration": "EXTRACT from evidence or estimate from green_flags",
      "description": ["Use tailored_resume.experience items, add metrics from quantified_impact"],
      "technologies": ["skills used in this role"]
    }}
  ],
  "projects": [
    {{
      "name": "EXTRACT project name from tailored_resume.projects",
      "description": "EXTRACT full description",
      "technologies": ["technologies mentioned in project description"],
      "highlights": ["Include downloads/metrics from quantified_impact", "other achievements", "technical highlights"]
    }}
  ],
  "education": [
    {{
      "degree": "EXTRACT from career_progression evidence (B.Tech, M.E., etc.)",
      "field": "EXTRACT field from evidence or 'Computer Science'",
      "institution": "EXTRACT university/institute name from evidence",
      "duration": "EXTRACT years from evidence",
      "gpa": "EXTRACT CGPA if mentioned in evidence"
    }}
  ],
  "achievements": ["EXTRACT ALL from quantified_impact evidence with numbers"],
  "certifications": [
    {{
      "name": "Relevant certification based on top skills",
      "issuer": "Legitimate issuer",
      "date": "Recent year"
    }}
  ],
  "languages": [
    {{
      "language": "English/Hindi based on location",
      "proficiency": "Native/Professional"
    }}
  ]
}}

Generate the best possible resume content now. Return ONLY valid JSON, no markdown formatting or explanation."""

        # Use Gemini 2.5 Pro - Best model for complex reasoning and resume generation
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Generate resume content with Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,  # Balanced creativity and accuracy
                top_p=0.9,
                top_k=40,
                max_output_tokens=8000,
            )
        )
        
        # Check if response is valid
        if not response.candidates or not response.candidates[0].content.parts:
            raise ValueError(f"Gemini response blocked or empty. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'}")
        
        # Parse Gemini response
        gemini_output = response.text.strip()
        
        # LOG: Print Gemini's raw response
        print("\n" + "=" * 80)
        print("🤖 GEMINI RAW RESPONSE:")
        print("=" * 80)
        print(gemini_output[:1500] if len(gemini_output) > 1500 else gemini_output)
        print(f"\n... (Total length: {len(gemini_output)} characters)")
        print("=" * 80 + "\n")
        
        # Clean up markdown code blocks if present
        if "```json" in gemini_output:
            gemini_output = gemini_output.split("```json")[1].split("```")[0].strip()
        elif "```" in gemini_output:
            gemini_output = gemini_output.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        try:
            resume_data_json = json.loads(gemini_output)
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from response
            json_match = re.search(r'\{.*\}', gemini_output, re.DOTALL)
            if json_match:
                resume_data_json = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse Gemini response as JSON: {str(e)}")
        
        # Build resume content from Gemini's output
        resume_content = ResumeBuilderContent(
            personal_info=resume_data_json.get("personal_info", {}),
            professional_summary=resume_data_json.get("professional_summary", ""),
            skills=resume_data_json.get("skills", {}),
            experience=resume_data_json.get("experience", []),
            projects=resume_data_json.get("projects", []),
            education=resume_data_json.get("education", []),
            achievements=resume_data_json.get("achievements", []),
            certifications=resume_data_json.get("certifications", []),
            languages=resume_data_json.get("languages", [])
        )
        
        # LOG: Print extracted personal info
        print("\n" + "=" * 80)
        print("👤 EXTRACTED PERSONAL INFO:")
        print("=" * 80)
        print(f"Name: {resume_data_json.get('personal_info', {}).get('name', 'N/A')}")
        print(f"Email: {resume_data_json.get('personal_info', {}).get('email', 'N/A')}")
        print(f"Phone: {resume_data_json.get('personal_info', {}).get('phone', 'N/A')}")
        print(f"Location: {resume_data_json.get('personal_info', {}).get('location', 'N/A')}")
        print(f"LinkedIn: {resume_data_json.get('personal_info', {}).get('linkedin', 'N/A')}")
        print(f"GitHub: {resume_data_json.get('personal_info', {}).get('github', 'N/A')}")
        print("=" * 80 + "\n")
        
        # Generate formatting tips using Gemini (non-critical, use fallback if fails)
        formatting_tips = [
            "Use strong action verbs to start each bullet point",
            "Quantify achievements with specific metrics and numbers",
            "Tailor keywords to match job descriptions for ATS optimization",
            "Keep formatting clean and consistent throughout",
            "Highlight technical skills prominently in a dedicated section",
            "Use reverse chronological order for experience and education",
            "Ensure contact information is current and professional"
        ]
        
        try:
            tips_prompt = f"""Based on this resume analysis, provide 5-7 specific, actionable formatting and content tips:

GREEN FLAGS (Strengths to leverage):
{json.dumps(analytics.key_takeaways.green_flags, indent=2)}

RED FLAGS (Areas to improve):
{json.dumps(analytics.key_takeaways.red_flags, indent=2)}

GAPS TO ADDRESS:
{json.dumps(enhancement.top_1_percent_gap.gaps, indent=2)}

Provide tips as a JSON array of strings. Each tip should be specific, actionable, and professional.
Format: ["tip1", "tip2", "tip3", ...]

Return ONLY the JSON array, no other text."""

            tips_response = model.generate_content(
                tips_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=1000,
                )
            )
            
            # Check if tips response is valid before accessing text
            if tips_response.candidates and tips_response.candidates[0].content.parts:
                tips_output = tips_response.text.strip()
                
                # Clean and parse tips
                if "```json" in tips_output:
                    tips_output = tips_output.split("```json")[1].split("```")[0].strip()
                elif "```" in tips_output:
                    tips_output = tips_output.split("```")[1].split("```")[0].strip()
                
                try:
                    parsed_tips = json.loads(tips_output)
                    if isinstance(parsed_tips, list) and len(parsed_tips) > 0:
                        formatting_tips = parsed_tips
                except json.JSONDecodeError:
                    pass  # Use fallback tips
        except Exception as e:
            # Log error but don't fail - use fallback tips
            import logging
            logging.warning(f"Failed to generate AI tips, using fallback: {str(e)}")
        
        # Add specific tips based on red/green flags
        if analytics.key_takeaways.red_flags:
            formatting_tips.append(f"⚠️ Address: {analytics.key_takeaways.red_flags[0]}")
        
        if analytics.key_takeaways.green_flags:
            formatting_tips.append(f"✅ Leverage: {analytics.key_takeaways.green_flags[0]}")
        
        return ResumeBuilderResponse(
            status="success",
            resume_content=resume_content,
            formatting_tips=formatting_tips[:10],  # Limit to top 10 tips
            message="AI-enhanced resume generated successfully using Gemini 2.5 Pro"
        )
        
    except Exception as e:
        import traceback
        error_detail = f"AI resume generation failed: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )
