from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class JobBase(BaseModel):
    title: str
    description: str
    department: str


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None


class Job(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

