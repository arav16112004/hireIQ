from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class InterviewBase(BaseModel):
    candidate_id: int
    transcript: str
    engagement_score: float = Field(ge=0.0, le=1.0)
    ai_score: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    transcript: Optional[str] = None
    engagement_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    ai_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None


class Interview(InterviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# OA RESULTS SCHEMAS
# ============================================================

class OAResultBase(BaseModel):
    candidate_id: int
    status: str = Field(default="pending", pattern="^(pending|pass|fail)$")


class OAResultCreate(OAResultBase):
    pass


class OAResultUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    status: Optional[str] = Field(None, pattern="^(pending|pass|fail)$")
    completed_at: Optional[datetime] = None


class OAResult(OAResultBase):
    id: int
    score: Optional[float] = None
    sent_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# FINAL INTERVIEW SCHEMAS
# ============================================================

class FinalInterviewBase(BaseModel):
    candidate_id: int
    recruiter_name: str
    recruiter_email: str
    scheduled_date: datetime
    decision: str = Field(default="pending", pattern="^(pending|pass|fail)$")


class FinalInterviewCreate(FinalInterviewBase):
    pass


class FinalInterviewUpdate(BaseModel):
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    decision: Optional[str] = Field(None, pattern="^(pending|pass|fail)$")
    feedback: Optional[str] = None


class FinalInterview(FinalInterviewBase):
    id: int
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

