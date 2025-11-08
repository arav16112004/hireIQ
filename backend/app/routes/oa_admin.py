"""
OA Platform Admin Routes - Question and assessment management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.db import oa_client
from app.db.schemas.oa import QuestionCreate, QuestionUpdate, TestCase
from app.core.logger import logger


router = APIRouter(prefix="/oa/admin", tags=["OA Admin"])


# ============================================================
# REQUEST MODELS
# ============================================================

class CreateQuestionRequest(BaseModel):
    title: str
    description: str
    difficulty: str = "medium"
    language: str
    time_limit: float = 5.0
    memory_limit: int = 128000
    points: int = 100
    starter_code: Optional[str] = None
    test_cases: List[TestCase]


class UpdateQuestionRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    language: Optional[str] = None
    time_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    points: Optional[int] = None
    starter_code: Optional[str] = None
    is_active: Optional[bool] = None


class AddTestCaseRequest(BaseModel):
    question_id: int
    input: str
    expected_output: str
    is_hidden: bool = False
    points: int = 1


# ============================================================
# QUESTION MANAGEMENT
# ============================================================

@router.get("/questions")
def list_all_questions(active_only: bool = False):
    """
    List all questions in the question bank
    
    Args:
        active_only: If True, only return active questions
    """
    try:
        questions = oa_client.get_all_questions(active_only=active_only)
        
        return {
            "total": len(questions),
            "questions": questions
        }
        
    except Exception as e:
        logger.error(f"Error listing questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/questions/{question_id}")
def get_question_admin(question_id: int):
    """
    Get question details including all test cases (including hidden)
    """
    try:
        question = oa_client.get_question(question_id, include_test_cases=True)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return question
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/questions")
def create_question(request: CreateQuestionRequest):
    """
    Create a new coding question with test cases
    """
    try:
        # Create the question
        question_id = oa_client.create_question(
            title=request.title,
            description=request.description,
            difficulty=request.difficulty,
            language=request.language,
            time_limit=request.time_limit,
            memory_limit=request.memory_limit,
            points=request.points,
            starter_code=request.starter_code,
            is_active=True
        )
        
        # Create test cases
        test_case_ids = []
        for tc in request.test_cases:
            tc_id = oa_client.create_test_case(
                question_id=question_id,
                input_data=tc.input,
                expected_output=tc.expected_output,
                is_hidden=tc.is_hidden,
                points=tc.points
            )
            test_case_ids.append(tc_id)
        
        logger.info(
            f"Question {question_id} created with {len(test_case_ids)} test cases"
        )
        
        return {
            "question_id": question_id,
            "test_case_ids": test_case_ids,
            "message": "Question created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/questions/{question_id}")
def update_question(question_id: int, request: UpdateQuestionRequest):
    """
    Update an existing question
    """
    try:
        # Check if question exists
        question = oa_client.get_question(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Update question
        updates = request.dict(exclude_unset=True)
        success = oa_client.update_question(question_id, **updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="No updates applied")
        
        logger.info(f"Question {question_id} updated")
        
        return {
            "question_id": question_id,
            "message": "Question updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/questions/{question_id}")
def delete_question(question_id: int):
    """
    Soft delete a question (sets is_active to False)
    """
    try:
        success = oa_client.delete_question(question_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Question not found")
        
        logger.info(f"Question {question_id} deactivated")
        
        return {
            "question_id": question_id,
            "message": "Question deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# TEST CASE MANAGEMENT
# ============================================================

@router.get("/questions/{question_id}/test-cases")
def get_test_cases(question_id: int):
    """Get all test cases for a question"""
    try:
        test_cases = oa_client.get_test_cases(question_id, include_hidden=True)
        
        return {
            "question_id": question_id,
            "total": len(test_cases),
            "test_cases": test_cases
        }
        
    except Exception as e:
        logger.error(f"Error getting test cases for question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-cases")
def add_test_case(request: AddTestCaseRequest):
    """Add a new test case to a question"""
    try:
        # Verify question exists
        question = oa_client.get_question(request.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        test_case_id = oa_client.create_test_case(
            question_id=request.question_id,
            input_data=request.input,
            expected_output=request.expected_output,
            is_hidden=request.is_hidden,
            points=request.points
        )
        
        logger.info(f"Test case {test_case_id} added to question {request.question_id}")
        
        return {
            "test_case_id": test_case_id,
            "message": "Test case added successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding test case: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/test-cases/{test_case_id}")
def delete_test_case(test_case_id: int):
    """Delete a test case"""
    try:
        success = oa_client.delete_test_case(test_case_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        logger.info(f"Test case {test_case_id} deleted")
        
        return {
            "test_case_id": test_case_id,
            "message": "Test case deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting test case {test_case_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# STATISTICS & MONITORING
# ============================================================

@router.get("/stats")
def get_question_bank_stats():
    """Get statistics about the question bank"""
    try:
        stats = oa_client.get_question_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting question bank stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
def list_all_sessions(status: Optional[str] = None, limit: int = 100):
    """
    List all OA sessions (for monitoring/admin purposes)
    
    Args:
        status: Filter by status (pending, in_progress, completed, expired)
        limit: Maximum number of sessions to return
    """
    try:
        # This would require a new function in oa_client to get all sessions
        # For now, return a placeholder
        
        return {
            "message": "Session listing not yet implemented",
            "requested_status": status,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/detailed")
def get_session_detailed_report(session_id: int):
    """
    Get detailed report for an OA session including all submissions and results
    """
    try:
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get candidate info
        from app.db import snowflake_client
        candidate = snowflake_client.get_candidate(session['CANDIDATE_ID'])
        
        # Get all submissions
        submissions = oa_client.get_submissions_by_session(session_id)
        
        # Get questions
        question_ids = session.get('QUESTION_IDS', [])
        questions = []
        for qid in question_ids:
            question = oa_client.get_question(qid, include_test_cases=True)
            if question:
                questions.append(question)
        
        return {
            "session": session,
            "candidate": candidate,
            "questions": questions,
            "submissions": submissions,
            "total_submissions": len(submissions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed report for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

