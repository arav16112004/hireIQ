"""
OA Platform Routes - Candidate-facing endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import secrets

from app.db import oa_client, snowflake_client
from app.services import grading_service
from app.core.logger import logger
from app.utils.auth_utils import get_current_user


router = APIRouter(prefix="/oa", tags=["OA Platform"])

# In-memory storage for session tokens (in production, use Redis or DB)
_session_tokens = {}  # {token: session_id}


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
    max_cheating_score: Optional[float] = None  # Highest integrity/cheating score during session


class AccessOARequest(BaseModel):
    candidate_id: int
    token: str
    session_id: Optional[int] = None  # Optional session_id from URL path


# ============================================================
# PUBLIC ENDPOINTS (No Auth Required)
# ============================================================

@router.post("/access")
def access_oa_from_email(request: AccessOARequest):
    """
    Public endpoint to access OA session from email link
    
    This endpoint verifies the token and returns session info without requiring authentication.
    The frontend should then prompt user to login/register if not already authenticated.
    
    Note: If token is invalid (e.g., server restart), we fall back to verifying session_id
    and candidate_id match directly from the database.
    """
    try:
        session_id = None
        
        # Priority 1: Use session_id from request if provided (from URL path)
        if request.session_id:
            session_id = request.session_id
            logger.info(f"Using session_id from request: {session_id}")
        
        # Priority 2: Try to get session_id from token
        elif request.token in _session_tokens:
            session_id = _session_tokens[request.token]
            logger.info(f"Token verified for session {session_id}")
        else:
            # Token not in memory (server restart or token expired)
            logger.warning(f"Token not found in memory: {request.token}")
            
            # Priority 3: Fallback - find session by candidate_id
            # Get all sessions for this candidate and find the most recent pending/in_progress one
            logger.info(f"Attempting fallback verification with candidate_id={request.candidate_id}")
            sessions = oa_client.get_sessions_by_candidate(request.candidate_id)
            if not sessions:
                raise HTTPException(
                    status_code=404,
                    detail="No assessment sessions found for this candidate."
                )
            
            # Find the most recent pending or in_progress session
            active_sessions = [
                s for s in sessions 
                if s.get('STATUS') in ('pending', 'PENDING', 'in_progress', 'IN_PROGRESS')
            ]
            if not active_sessions:
                # If no active sessions, use the most recent one
                session_id = sessions[0].get('ID')
                logger.info(f"No active sessions found, using most recent session {session_id}")
            else:
                # Use the most recent active session
                session_id = active_sessions[0].get('ID')
                logger.info(f"Found active session {session_id} for candidate {request.candidate_id}")
        
        # Get session details
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify the candidate_id matches (critical security check)
        session_candidate_id = session.get('CANDIDATE_ID') or session.get('candidate_id')
        request_candidate_id = request.candidate_id
        
        # Convert both to int for comparison (in case one is string)
        try:
            session_candidate_id = int(session_candidate_id) if session_candidate_id is not None else None
            request_candidate_id = int(request_candidate_id) if request_candidate_id is not None else None
        except (ValueError, TypeError):
            logger.error(f"Invalid candidate_id types: session={session_candidate_id}, request={request.candidate_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid candidate ID format"
            )
        
        if session_candidate_id != request_candidate_id:
            logger.warning(
                f"Candidate ID mismatch for session {session_id}: "
                f"session_candidate_id={session_candidate_id} (type: {type(session_candidate_id)}), "
                f"request_candidate_id={request_candidate_id} (type: {type(request_candidate_id)})"
            )
            logger.warning(f"Full session data: {session}")
            
            # If candidate_id doesn't match, but we have session_id from URL, 
            # we can still allow access if the session exists (token might be wrong but session is valid)
            # This handles cases where the email link has wrong candidate_id but correct session_id
            if request.session_id and request.session_id == session_id:
                logger.info(
                    f"Allowing access despite candidate_id mismatch because session_id matches. "
                    f"Session {session_id} exists and is valid."
                )
                # Continue - don't raise error
            else:
                raise HTTPException(
                    status_code=403,
                    detail=f"Invalid access credentials. Session belongs to candidate {session_candidate_id}, but request is for candidate {request_candidate_id}."
                )
        
        # Check if session is still valid
        status = session.get('STATUS')
        if status == 'completed':
            raise HTTPException(
                status_code=400,
                detail="This assessment has already been completed"
            )
        
        if status == 'expired':
            raise HTTPException(
                status_code=400,
                detail="This assessment link has expired"
            )
        
        # Get candidate info
        candidate = snowflake_client.get_candidate(request.candidate_id)
        if not candidate:
            logger.error(f"Candidate {request.candidate_id} not found for session {session_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        logger.info(
            f"OA access verified for session {session_id}, candidate {request.candidate_id} "
            f"({candidate.get('EMAIL')}), status: {status}"
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "candidate_id": request.candidate_id,
            "candidate_email": candidate.get('EMAIL'),
            "candidate_name": candidate.get('NAME'),
            "status": status,
            "message": "Access verified. Please login to continue."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing OA from email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/public")
def get_oa_session_public(session_id: int, token: str):
    """
    Public endpoint to get session details with token verification (no auth required)
    
    This allows accessing session info before authentication
    """
    try:
        # Verify token
        if token not in _session_tokens or _session_tokens[token] != session_id:
            raise HTTPException(
                status_code=403,
                detail="Invalid access token"
            )
        
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get candidate info
        candidate_id = session['CANDIDATE_ID']
        candidate = snowflake_client.get_candidate(candidate_id)
        
        return {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "candidate_email": candidate.get('EMAIL') if candidate else None,
            "status": session.get('STATUS'),
            "duration_minutes": session.get('DURATION_MINUTES'),
            "question_ids": session.get('QUESTION_IDS', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CANDIDATE ENDPOINTS (Auth Required)
# ============================================================

@router.post("/start")
def start_oa_assessment(request: StartOARequest, current_user: dict = Depends(get_current_user)):
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
def get_oa_session(session_id: int, current_user: dict = Depends(get_current_user)):
    """Get details about an OA session (requires authentication)"""
    try:
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify the authenticated user is the candidate for this session
        candidate_id = session.get('CANDIDATE_ID')
        candidate = snowflake_client.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Check if the current user's email matches the candidate's email (case-insensitive)
        user_email = current_user.get('email', '').lower()
        candidate_email = candidate.get('EMAIL', '').lower()
        if user_email != candidate_email:
            logger.warning(
                f"Email mismatch for session {session_id}: "
                f"user_email={current_user.get('email')}, candidate_email={candidate.get('EMAIL')}"
            )
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this assessment"
            )
        
        # Auto-start the session if it's still pending
        status = session.get('STATUS')
        if status == 'pending':
            oa_client.start_oa_session(session_id)
            session = oa_client.get_oa_session(session_id)  # Refresh to get updated status
            logger.info(f"Auto-started OA session {session_id} for candidate {candidate_id}")
        
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
def submit_code(request: SubmitCodeRequest):
    """
    Submit code for a question in an OA session
    
    Creates submission and grades it using Judge0 synchronously
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
        
        # Grade submission synchronously to get immediate results
        logger.info(f"Grading submission {submission_id} synchronously...")
        try:
            grading_results = grading_service.grade_submission(submission_id)
        except Exception as e:
            logger.error(f"Grading service error: {str(e)}", exc_info=True)
            return {
                "submission_id": submission_id,
                "status": "error",
                "error": f"Grading error: {str(e)}",
                "passed": 0,
                "total": 0
            }
        
        if not grading_results.get('success'):
            return {
                "submission_id": submission_id,
                "status": "error",
                "error": grading_results.get('error', 'Grading failed'),
                "passed": 0,
                "total": 0
            }
        
        # Get submission for output details
        submission = oa_client.get_submission(submission_id)
        
        # Extract test results for detailed output
        test_results = grading_results.get('results', {})
        
        # Get raw output from first test case
        raw_output = ""
        if test_results.get('test_results') and len(test_results['test_results']) > 0:
            first_test = test_results['test_results'][0]
            raw_output = str(first_test.get('stdout', '')).strip()
        
        # Format test cases for frontend
        test_cases_data = []
        if test_results.get('compile_error'):
            compile_error = str(test_results.get('compile_output', 'Compilation failed'))
        else:
            compile_error = None
            if test_results.get('test_results'):
                for i, tr in enumerate(test_results['test_results'][:3]):
                    test_cases_data.append({
                        'number': i + 1,
                        'passed': tr.get('passed', False),
                        'status': tr.get('status', ''),
                        'input': str(tr.get('input', '')).strip(),
                        'output': str(tr.get('stdout', '')).strip(),
                        'expected': str(tr.get('expected_output', '')).strip(),
                        'error': str(tr.get('stderr', '')).strip() if tr.get('stderr') else None,
                        'time': tr.get('time'),
                        'memory': tr.get('memory')
                    })
        
        # Return results immediately
        return {
            "submission_id": submission_id,
            "status": "completed",
            "passed": grading_results.get('passed_tests', 0),
            "total": grading_results.get('total_tests', 0),
            "score": grading_results.get('score', 0),
            "raw_output": raw_output,
            "compile_error": compile_error,
            "test_cases": test_cases_data,
            "execution_time": grading_results.get('execution_time'),
            "memory_used": grading_results.get('memory_used')
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


@router.get("/session/{session_id}/results")
def get_session_results(session_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get comprehensive results for a completed OA session
    
    Returns score breakdown, question results, and overall performance
    """
    try:
        # Get session
        session = oa_client.get_oa_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify user owns this session
        candidate_id = session.get('CANDIDATE_ID')
        candidate = snowflake_client.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        user_email = current_user.get('email', '').lower()
        candidate_email = candidate.get('EMAIL', '').lower()
        if user_email != candidate_email:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view these results"
            )
        
        # Log session data for debugging
        logger.info(f"📊 Session {session_id} data: SCORE={session.get('SCORE')}, MAX_SCORE={session.get('MAX_SCORE')}, STATUS={session.get('STATUS')}")
        
        # Calculate session score using grading service
        score_result = grading_service.calculate_session_score(session_id)
        
        if not score_result['success']:
            logger.error(f"❌ Failed to calculate score for session {session_id}: {score_result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=score_result.get('error', 'Failed to calculate score')
            )
        
        logger.info(f"✅ Score calculation result: {score_result.get('percentage', 0):.2f}% (source: {score_result.get('source', 'unknown')})")
        
        # Get questions and submissions
        question_ids = session.get('QUESTION_IDS', [])
        submissions = oa_client.get_submissions_by_session(session_id)
        questions = []
        question_results = []
        
        # If session has SCORE/MAX_SCORE set, distribute the score evenly across questions
        # Otherwise, calculate from submissions
        session_has_scores = score_result.get('source') == 'session_scores'
        overall_percentage = score_result['percentage']
        total_score = score_result['total_score']
        max_score = score_result['max_score']
        
        if session_has_scores and len(question_ids) > 0:
            # Session scores are set - use the overall percentage for each question
            # When session has overall score, we apply the same percentage to all questions
            for idx, qid in enumerate(question_ids):
                question = oa_client.get_question(qid, include_test_cases=False)
                if question:
                    question_max_score = float(question.get('POINTS', 100))
                    # Use the overall percentage directly for each question
                    question_percentage = overall_percentage
                    # Calculate the raw score that would give this percentage
                    question_score = (question_percentage / 100.0) * question_max_score
                    
                    question_results.append({
                        "question_id": qid,
                        "question_title": question.get('TITLE', f"Question {idx + 1}"),
                        "score": question_percentage,
                        "raw_score": question_score,
                        "max_score": question_max_score,
                        "passed": question_percentage >= 70,
                        "test_cases_passed": 0,  # Unknown if using session scores
                        "total_test_cases": 0,
                        "execution_time": None,
                    })
        else:
            # Calculate from submissions
            for qid in question_ids:
                question = oa_client.get_question(qid, include_test_cases=False)
                if question:
                    questions.append(question)
                    
                    # Find best submission for this question
                    question_submissions = [s for s in submissions if s.get('QUESTION_ID') == qid]
                    best_submission = None
                    if question_submissions:
                        try:
                            best_submission = max(
                                question_submissions,
                                key=lambda s: float(s.get('SCORE', 0) or 0)
                            )
                        except (ValueError, TypeError):
                            pass
                    
                    # Calculate question score
                    question_max_score = float(question.get('POINTS', 100))
                    question_score = float(best_submission.get('SCORE', 0) or 0) if best_submission else 0
                    question_percentage = (question_score / question_max_score * 100) if question_max_score > 0 else 0
                    
                    question_results.append({
                        "question_id": qid,
                        "question_title": question.get('TITLE', f"Question {qid}"),
                        "score": question_percentage,
                        "raw_score": question_score,
                        "max_score": question_max_score,
                        "passed": question_percentage >= 70,
                        "test_cases_passed": best_submission.get('PASSED_TESTS', 0) if best_submission else 0,
                        "total_test_cases": best_submission.get('TOTAL_TESTS', 0) if best_submission else 0,
                        "execution_time": best_submission.get('EXECUTION_TIME') if best_submission else None,
                    })
        
        return {
            "session_id": session_id,
            "overall_score": overall_percentage,
            "total_score": score_result['total_score'],
            "max_score": score_result['max_score'],
            "percentage": overall_percentage,
            "passed": overall_percentage >= 70,
            "questions": question_results,
            "questions_attempted": score_result['questions_attempted'],
            "total_questions": score_result['total_questions'],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
def complete_oa_session(request: CompleteSessionRequest, current_user: dict = Depends(get_current_user)):
    """
    Complete an OA session and calculate final results
    
    Updates candidate stage based on performance
    Saves the highest cheating/integrity score from the session
    """
    try:
        result = grading_service.complete_oa_session_with_results(
            session_id=request.session_id,
            max_cheating_score=request.max_cheating_score
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


@router.get("/my-sessions")
def get_my_oa_sessions(current_user: dict = Depends(get_current_user)):
    """
    Get all OA sessions for the current logged-in user
    """
    try:
        # Get candidate by email (case-insensitive)
        user_email = current_user.get('email')
        if not user_email:
            logger.warning(f"No email found in current_user: {current_user}")
            return {
                "sessions": [],
                "message": "No email found in user account"
            }
        
        logger.info(f"=== FETCHING OA SESSIONS ===")
        logger.info(f"User email: {user_email}")
        logger.info(f"Current user dict: {current_user}")
        
        # Find candidate_id from email using snowflake_client (case-insensitive)
        with snowflake_client.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get ALL candidate IDs for this email (user might have multiple applications)
            cursor.execute(
                "SELECT ID, EMAIL FROM CANDIDATES WHERE UPPER(EMAIL) = UPPER(%s)",
                (user_email,)
            )
            candidates = cursor.fetchall()
            
            if not candidates:
                logger.warning(f"❌ No candidate record found for email: {user_email}")
                # Return empty sessions instead of error - user might not have applied yet
                return {
                    "sessions": [],
                    "user_email": user_email,
                    "message": f"No candidate record found for email {user_email}. You may need to apply for a job first."
                }
            
            # Extract all candidate IDs
            candidate_ids = [c[0] for c in candidates]
            logger.info(f"✅ Found {len(candidate_ids)} candidate record(s) for email: {user_email}")
            logger.info(f"   Candidate IDs: {candidate_ids}")
            
            # Get all sessions for ALL candidate IDs (user might have multiple applications)
            logger.info(f"Querying OA_SESSIONS for candidate_ids: {candidate_ids}")
            if len(candidate_ids) == 1:
                # Single candidate - use simple query
                cursor.execute(
                    """
                    SELECT * FROM OA_SESSIONS 
                    WHERE CANDIDATE_ID = %s
                    ORDER BY CREATED_AT DESC
                    """,
                    (candidate_ids[0],)
                )
            else:
                # Multiple candidates - use IN clause
                placeholders = ','.join(['%s'] * len(candidate_ids))
                cursor.execute(
                    f"""
                    SELECT * FROM OA_SESSIONS 
                    WHERE CANDIDATE_ID IN ({placeholders})
                    ORDER BY CREATED_AT DESC
                    """,
                    candidate_ids
                )
            rows = cursor.fetchall()
            
            logger.info(f"Raw query returned {len(rows) if rows else 0} rows")
            
            # Convert to dict format
            sessions = []
            if rows:
                columns = [desc[0] for desc in cursor.description]
                logger.info(f"Session columns: {columns}")
                for row in rows:
                    session = dict(zip(columns, row))
                    # Handle QUESTION_IDS if it's a JSON string
                    if 'QUESTION_IDS' in session and isinstance(session['QUESTION_IDS'], str):
                        try:
                            import json
                            session['QUESTION_IDS'] = json.loads(session['QUESTION_IDS'])
                        except Exception as e:
                            logger.warning(f"Failed to parse QUESTION_IDS: {e}")
                            session['QUESTION_IDS'] = []
                    sessions.append(session)
                    logger.info(f"  - Session ID: {session.get('ID')}, Status: {session.get('STATUS')}, Candidate: {session.get('CANDIDATE_ID')}")
            else:
                # Check if there are any sessions at all
                cursor.execute("SELECT COUNT(*) FROM OA_SESSIONS")
                total_sessions = cursor.fetchone()[0]
                logger.info(f"No sessions found for candidate_ids {candidate_ids}. Total sessions in database: {total_sessions}")
                
                # Check what candidate_ids have sessions
                cursor.execute("SELECT DISTINCT CANDIDATE_ID FROM OA_SESSIONS LIMIT 10")
                candidates_with_sessions = cursor.fetchall()
                logger.info(f"Candidates with sessions: {[c[0] for c in candidates_with_sessions]}")
                logger.info(f"   Your candidate IDs: {candidate_ids}")
                logger.info(f"   Overlap: {set(candidate_ids) & set([c[0] for c in candidates_with_sessions])}")
            
            cursor.close()
        
        logger.info(f"=== RETURNING OA SESSIONS ===")
        logger.info(f"Sessions count: {len(sessions)}")
        logger.info(f"Candidate IDs: {candidate_ids}")
        logger.info(f"User email: {user_email}")
        
        # Return the primary candidate_id (first one) for backwards compatibility
        primary_candidate_id = candidate_ids[0] if candidate_ids else None
        
        return {
            "sessions": sessions,
            "candidate_id": primary_candidate_id,
            "candidate_ids": candidate_ids,  # Include all candidate IDs
            "user_email": user_email  # Include for debugging
        }
        
    except Exception as e:
        logger.error(f"Error getting sessions for user {current_user.get('email')}: {str(e)}", exc_info=True)
        # Return empty sessions instead of raising error - don't break the dashboard
        return {
            "sessions": [],
            "message": f"Error fetching sessions: {str(e)}"
        }


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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_oa_token(session_id: int) -> str:
    """
    Generate a secure token for OA session access
    
    Args:
        session_id: The OA session ID
        
    Returns:
        Secure token string
    """
    token = secrets.token_urlsafe(32)
    _session_tokens[token] = session_id
    logger.info(f"Generated token for session {session_id}")
    return token


def get_oa_link(session_id: int, candidate_id: int, base_url: str = None) -> str:
    """
    Generate OA link with token for email
    
    Args:
        session_id: OA session ID
        candidate_id: Candidate ID
        base_url: Base URL for frontend (defaults to localhost)
        
    Returns:
        Complete OA link
    """
    token = generate_oa_token(session_id)
    base_url = base_url or "http://localhost:3000"
    
    # Remove trailing slash and any existing /oa/ path to avoid double /oa/oa/
    base_url = base_url.rstrip('/')
    if base_url.endswith('/oa'):
        base_url = base_url[:-3]
    
    return f"{base_url}/oa/{session_id}?candidate_id={candidate_id}&token={token}"

