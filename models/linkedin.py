# models.py
from pydantic import BaseModel
from typing import List, Optional

class LinkedinDateInfo(BaseModel):
    year: int
    month: int
    day: int

class LinkedinGeo(BaseModel):
    country: str
    city: str
    full: str

class LinkedinEducation(BaseModel):
    start: LinkedinDateInfo
    end: LinkedinDateInfo
    fieldOfStudy: str
    degree: str
    grade: str
    schoolName: str
    description: str
    activities: str
    url: str
    schoolId: str

class LinkedinPosition(BaseModel):
    companyName: str
    companyUsername: str
    companyURL: str
    companyLogo: str
    companyIndustry: str
    companyStaffCountRange: str
    title: str
    location: str
    description: str
    employmentType: str
    start: LinkedinDateInfo
    end: Optional[LinkedinDateInfo] = None

class LinkedinLocaleSupport(BaseModel):
    country: str
    language: str

class Language(BaseModel):
    name: str
    proficiency: str

class Skill(BaseModel):
    name: str
    proficiency: Optional[str] = None
    hasSkillAssessment: Optional[bool] = None

class Position(BaseModel):
    title: str
    companyName: str
    location: str
    description: str
    employmentType: Optional[str] = "Full-time"
    start: LinkedinDateInfo
    end: Optional[LinkedinDateInfo] = None

class Certification(BaseModel):
    name: str

class Project(BaseModel):
    title: str
    description: str
    start: LinkedinDateInfo
    end: Optional[LinkedinDateInfo] = None

class LinkedinProject(BaseModel):
    total: Optional[int] = 0  # Make total optional with default value
    items: Optional[List[Project]] = []  # Default to empty list

class LinkedinProfile(BaseModel):
    id: int
    urn: str
    firstName: str
    lastName: str
    username: str
    summary: str
    headline: str
    isOpenToWork: Optional[bool] = None
    isHiring: Optional[bool] = None
    languages: List[Language] = []  # Add default empty list
    skills: List[Skill] = []  # Add default empty list
    position: List[Position] = []  # Add default empty list
    certifications: List[Certification] = []  # Add default empty list
    projects: Optional[LinkedinProject] = None  # Make projects entirely optional

    @classmethod
    def parse_obj(cls, obj: dict):
        # Add defensive programming for missing sections
        obj_copy = obj.copy()  # Create a copy to avoid modifying the original
        
        # Handle missing or None sections with empty lists
        obj_copy['languages'] = [Language(**lang) for lang in obj_copy.get('languages', [])] if obj_copy.get('languages') else []
        obj_copy['skills'] = [Skill(**skill) for skill in obj_copy.get('skills', [])] if obj_copy.get('skills') else []
        obj_copy['position'] = [Position(**pos) for pos in obj_copy.get('position', [])] if obj_copy.get('position') else []
        obj_copy['certifications'] = [Certification(**cert) for cert in obj_copy.get('certifications', [])] if obj_copy.get('certifications') else []
        
        # Handle projects section
        projects_data = obj_copy.get('projects', {})
        if projects_data and isinstance(projects_data, dict):
            # If projects exist and is a dict, parse it
            obj_copy['projects'] = LinkedinProject(
                total=projects_data.get('total', 0),
                items=[Project(**proj) for proj in projects_data.get('items', [])] if projects_data.get('items') else []
            )
        else:
            # If no projects or invalid format, set to None
            obj_copy['projects'] = None
            
        return super().parse_obj(obj_copy)
    id: int
    urn: str
    firstName: str
    lastName: str
    username: str
    summary: str
    headline: str
    isOpenToWork: Optional[bool] = None
    isHiring: Optional[bool] = None
    languages: List[Language]
    skills: List[Skill]
    position: List[Position]
    certifications: List[Certification]
    projects: LinkedinProject

    @classmethod
    def parse_obj(cls, obj: dict):
        # Ensure languages, skills, positions, certifications, and projects are parsed correctly
        obj['languages'] = [Language(**lang) for lang in obj.get('languages', [])]
        obj['skills'] = [Skill(**skill) for skill in obj.get('skills', [])]
        obj['position'] = [Position(**pos) for pos in obj.get('position', [])]
        obj['certifications'] = [Certification(**cert) for cert in obj.get('certifications', [])]
        obj['projects'] = LinkedinProject(**obj.get('projects', {}))
        return super().parse_obj(obj)