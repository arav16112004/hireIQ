from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    resume_url: str
    job_id: int


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    resume_url: Optional[str] = None
    fit_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    stage: Optional[str] = Field(None, pattern="^(applied|oa_sent|oa_passed|ai_passed|final)$")


class Candidate(CandidateBase):
    id: int
    fit_score: Optional[float] = None
    stage: str = "applied"
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateWithJob(Candidate):
    job_title: Optional[str] = None
    job_department: Optional[str] = None

