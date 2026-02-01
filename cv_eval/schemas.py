from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class CVEvaluationRequest(BaseModel):
    cv_text: str = Field(..., description="CV text content")
    jd_text: str = Field(..., description="Job description text content")

class CVEvaluationResult(BaseModel):
    cv_quality: Dict[str, Any] = Field(..., description="CV quality scores")
    jd_match: Optional[Dict[str, Any]] = Field(None, description="JD match scores")
    fit_index: Optional[Dict[str, Any]] = Field(None, description="Overall fit index")

# ---------- Universal Resume Contract Schemas ----------

class ResumeLocation(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None

class ResumeProfile(BaseModel):
    network: str
    username: Optional[str] = None
    url: str

class ResumeBasics(BaseModel):
    name: str = "Candidate Name"
    label: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[ResumeLocation] = None
    profiles: List[ResumeProfile] = Field(default_factory=list)

class ResumeDateRange(BaseModel):
    start: Optional[str] = None
    end: Optional[Any] = None  # string date or "present"

class ResumeTimelineItem(BaseModel):
    title: str
    organization: str
    location: Optional[str] = None
    date: Optional[ResumeDateRange] = None
    summary: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

class ResumeSkillItem(BaseModel):
    name: str
    level: Optional[str] = None  # beginner, intermediate, advanced, expert
    keywords: List[str] = Field(default_factory=list)

class ResumeProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    role: Optional[str] = None
    date: Optional[ResumeDateRange] = None
    highlights: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None

class ResumeSimpleListItem(BaseModel):
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None

class ResumeCustomSection(BaseModel):
    title: str
    content: List[str] = Field(default_factory=list)

class ResumeSections(BaseModel):
    skills: List[ResumeSkillItem] = Field(default_factory=list)
    work: List[ResumeTimelineItem] = Field(default_factory=list)
    education: List[ResumeTimelineItem] = Field(default_factory=list)
    projects: List[ResumeProjectItem] = Field(default_factory=list)
    achievements: List[ResumeSimpleListItem] = Field(default_factory=list)
    certifications: List[ResumeSimpleListItem] = Field(default_factory=list)
    publications: List[ResumeSimpleListItem] = Field(default_factory=list)
    volunteering: List[ResumeTimelineItem] = Field(default_factory=list)
    custom: Dict[str, ResumeCustomSection] = Field(default_factory=dict)

class ResumeMeta(BaseModel):
    language: str = "en"
    lastUpdated: Optional[str] = None
    visibility: Dict[str, bool] = Field(default_factory=dict)

class UniversalResume(BaseModel):
    basics: ResumeBasics
    sections: ResumeSections
    meta: ResumeMeta = Field(default_factory=ResumeMeta)