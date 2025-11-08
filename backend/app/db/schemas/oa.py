from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============================================================
# QUESTION SCHEMAS
# ============================================================

class TestCase(BaseModel):
    """Test case for a coding question"""
    input: str
    expected_output: str
    is_hidden: bool = False  # Hidden test cases not shown to candidates
    points: int = 1


class QuestionBase(BaseModel):
    title: str
    description: str
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    language: str  # python, javascript, java, etc.
    time_limit: float = 5.0  # seconds
    memory_limit: int = 128000  # KB
    points: int = 100
    starter_code: Optional[str] = None


class QuestionCreate(QuestionBase):
    test_cases: List[TestCase]


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    language: Optional[str] = None
    time_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    points: Optional[int] = None
    starter_code: Optional[str] = None
    is_active: Optional[bool] = None


class Question(QuestionBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionWithTestCases(Question):
    test_cases: List[TestCase] = []


# ============================================================
# OA SESSION SCHEMAS
# ============================================================

class OASessionBase(BaseModel):
    candidate_id: int
    question_ids: List[int]  # List of question IDs for this assessment
    duration_minutes: int = 60  # Total time allowed
    

class OASessionCreate(OASessionBase):
    pass


class OASession(OASessionBase):
    id: int
    status: str = "pending"  # pending, in_progress, completed, expired
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# SUBMISSION SCHEMAS
# ============================================================

class SubmissionBase(BaseModel):
    session_id: int
    question_id: int
    source_code: str
    language: str


class SubmissionCreate(SubmissionBase):
    pass


class Submission(SubmissionBase):
    id: int
    status: str = "pending"  # pending, running, completed, error
    score: Optional[float] = None
    passed_tests: int = 0
    total_tests: int = 0
    execution_time: Optional[float] = None  # seconds
    memory_used: Optional[int] = None  # KB
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None
    submitted_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# CANDIDATE RESPONSE SCHEMAS (for API responses)
# ============================================================

class OASessionStart(BaseModel):
    """Response when candidate starts OA"""
    session_id: int
    questions: List[Question]  # Without test cases for security
    duration_minutes: int
    started_at: datetime
    expires_at: datetime


class SubmissionResult(BaseModel):
    """Response after code submission"""
    submission_id: int
    status: str
    passed_tests: int
    total_tests: int
    score: float
    execution_time: Optional[float] = None
    test_results: Optional[List[Dict[str, Any]]] = None  # May hide details


class OASessionResult(BaseModel):
    """Final OA result"""
    session_id: int
    candidate_id: int
    total_score: float
    max_score: float
    pass_rate: float
    completed_at: datetime
    submissions: List[Submission]


# ============================================================
# ADMIN SCHEMAS
# ============================================================

class QuestionBankStats(BaseModel):
    """Statistics about question bank"""
    total_questions: int
    by_difficulty: Dict[str, int]
    by_language: Dict[str, int]
    active_questions: int


class CandidateOAStats(BaseModel):
    """Statistics for a candidate's OA performance"""
    candidate_id: int
    total_sessions: int
    completed_sessions: int
    average_score: float
    total_submissions: int

