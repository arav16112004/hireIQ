"""
OA Platform Routes - Candidate-facing endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from app.db import oa_client, snowflake_client
from app.services import grading_service
from app.core.logger import logger


router = APIRouter(prefix="/oa", tags=["OA Platform"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class StartOARequest(BaseModel):
    candidate_id: int
    question_ids: List[int]
    duration_minutes: int = 60


class SubmitCodeRequest(BaseModel):
    session_id: int
    question_id: int
    source_code: str
    language: str


class CompleteSessionRequest(BaseModel):
    session_id: int


# ============================================================
# CANDIDATE ENDPOINTS
# ============================================================

@router.post("/start")
def start_oa_assessment(request: StartOARequest):
    """
    Start a new OA session for a candidate
    
    Creates an OA session and returns the questions (without hidden test cases)
    """
    try:
        # Verify candidate exists
        candidate = snowflake_client.get_candidate(request.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Verify all questions exist
        questions = []
        for qid in request.question_ids:
            question = oa_client.get_question(qid, include_test_cases=False)
            if not question:
                raise HTTPException(
                    status_code=404,
                    detail=f"Question {qid} not found"
                )
            questions.append(question)
        
        # Create OA session
        session_id = oa_client.create_oa_session(
            candidate_id=request.candidate_id,
            question_ids=request.question_ids,
            duration_minutes=request.duration_minutes
        )
        
        # Start the session
        oa_client.start_oa_session(session_id)
        
        # Calculate expiration time
        started_at = datetime.now()
        expires_at = started_at + timedelta(minutes=request.duration_minutes)
        
        logger.info(
            f"OA session {session_id} started for candidate {request.candidate_id}"
        )
        
        return {
            "session_id": session_id,
            "questions": questions,
            "duration_minutes": request.duration_minutes,
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "total_questions": len(questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting OA session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
def get_oa_session(session_id: int):
    """Get details about an OA session"""
    try:
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get questions for this session (without test cases for security)
        question_ids = session.get('QUESTION_IDS', [])
        questions = []
        for qid in question_ids:
            question = oa_client.get_question(qid, include_test_cases=False)
            if question:
                questions.append(question)
        
        return {
            "session": session,
            "questions": questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
def submit_code(request: SubmitCodeRequest, background_tasks: BackgroundTasks):
    """
    Submit code for a question in an OA session
    
    Creates submission and grades it using Judge0 in the background
    """
    try:
        # Verify session exists and is active
        session = oa_client.get_oa_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session['STATUS'] not in ['in_progress', 'pending']:
            raise HTTPException(
                status_code=400,
                detail=f"Session is {session['STATUS']}, cannot submit"
            )
        
        # Verify question is part of this session
        question_ids = session.get('QUESTION_IDS', [])
        if request.question_id not in question_ids:
            raise HTTPException(
                status_code=400,
                detail="Question not part of this session"
            )
        
        # Create submission
        submission_id = oa_client.create_submission(
            session_id=request.session_id,
            question_id=request.question_id,
            source_code=request.source_code,
            language=request.language
        )
        
        # Grade submission in background
        background_tasks.add_task(grading_service.grade_submission, submission_id)
        
        logger.info(
            f"Submission {submission_id} created for session {request.session_id}, "
            f"question {request.question_id}"
        )
        
        return {
            "submission_id": submission_id,
            "status": "pending",
            "message": "Code submitted successfully. Grading in progress..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submission/{submission_id}")
def get_submission_result(submission_id: int):
    """
    Get the result of a code submission
    
    Returns grading results including test case outcomes
    """
    try:
        submission = oa_client.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return {
            "submission_id": submission_id,
            "status": submission['STATUS'],
            "score": submission.get('SCORE'),
            "passed_tests": submission.get('PASSED_TESTS', 0),
            "total_tests": submission.get('TOTAL_TESTS', 0),
            "execution_time": submission.get('EXECUTION_TIME'),
            "memory_used": submission.get('MEMORY_USED'),
            "stdout": submission.get('STDOUT'),
            "stderr": submission.get('STDERR'),
            "compile_output": submission.get('COMPILE_OUTPUT'),
            "test_results": submission.get('TEST_RESULTS'),
            "submitted_at": submission.get('SUBMITTED_AT')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting submission {submission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/submissions")
def get_session_submissions(session_id: int):
    """Get all submissions for a session"""
    try:
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        submissions = oa_client.get_submissions_by_session(session_id)
        
        return {
            "session_id": session_id,
            "total_submissions": len(submissions),
            "submissions": submissions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting submissions for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
def complete_oa_session(request: CompleteSessionRequest):
    """
    Complete an OA session and calculate final results
    
    Updates candidate stage based on performance
    """
    try:
        result = grading_service.complete_oa_session_with_results(
            request.session_id
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to complete session')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing session {request.session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candidate/{candidate_id}/results")
def get_candidate_oa_results(candidate_id: int):
    """
    Get all OA results for a candidate
    
    Returns comprehensive OA history and statistics
    """
    try:
        results = grading_service.get_oa_results_for_candidate(candidate_id)
        
        if not results['success']:
            raise HTTPException(
                status_code=404,
                detail=results.get('error', 'Candidate not found')
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OA results for candidate {candidate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/question/{question_id}")
def get_question_details(question_id: int, include_hidden: bool = False):
    """
    Get question details
    
    By default, hidden test cases are excluded (for candidate view)
    """
    try:
        question = oa_client.get_question(question_id, include_test_cases=True)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Filter out hidden test cases if requested
        if not include_hidden and 'test_cases' in question:
            question['test_cases'] = [
                tc for tc in question['test_cases']
                if not tc.get('IS_HIDDEN', False)
            ]
        
        return question
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting question {question_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
def get_supported_languages():
    """Get list of supported programming languages"""
    from app.services.judge0_service import get_supported_languages
    
    return {
        "languages": get_supported_languages()
    }

