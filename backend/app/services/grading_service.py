"""
OA Grading Service
Handles code execution, grading, and updating results back to database
"""
from typing import Dict, Any, List, Optional
from app.services.judge0_service import judge0_client, run_test_cases
from app.db import oa_client, snowflake_client
from app.core.logger import logger


def grade_submission(submission_id: int) -> Dict[str, Any]:
    """
    Grade a code submission by running it through Judge0 and updating results
    
    Args:
        submission_id: ID of the submission to grade
    
    Returns:
        Dictionary with grading results
    """
    try:
        # Get submission details
        submission = oa_client.get_submission(submission_id)
        if not submission:
            return {
                "success": False,
                "error": "Submission not found"
            }
        
        # Get question and test cases
        question = oa_client.get_question(
            submission['QUESTION_ID'],
            include_test_cases=True
        )
        if not question:
            return {
                "success": False,
                "error": "Question not found"
            }
        
        test_cases = question.get('test_cases', [])
        if not test_cases:
            return {
                "success": False,
                "error": "No test cases found for this question"
            }
        
        # Prepare test cases for Judge0
        judge0_test_cases = []
        for tc in test_cases:
            judge0_test_cases.append({
                "input": tc.get('INPUT', ''),
                "expected_output": tc.get('EXPECTED_OUTPUT', '')
            })
        
        # Update submission status to running
        oa_client.update_submission(submission_id, status='running')
        
        # Run code through Judge0
        logger.info(f"Running submission {submission_id} through Judge0...")
        results = run_test_cases(
            source_code=submission['SOURCE_CODE'],
            language=submission['LANGUAGE'],
            test_cases=judge0_test_cases,
            time_limit=question.get('TIME_LIMIT', 5.0),
            memory_limit=question.get('MEMORY_LIMIT', 128000)
        )
        
        # Calculate score based on test results
        total_tests = results['total_tests']
        passed_tests = results['passed']
        question_points = float(question.get('POINTS', 100))
        
        # Score is proportional to passed tests
        score = (passed_tests / total_tests * question_points) if total_tests > 0 else 0
        
        # Get execution metrics (ensure all values are floats)
        times = [float(tr.get('time', 0)) for tr in results['test_results'] if tr.get('time') is not None]
        avg_time = sum(times) / len(times) if times else 0
        
        memories = [float(tr.get('memory', 0)) for tr in results['test_results'] if tr.get('memory') is not None]
        avg_memory = sum(memories) / len(memories) if memories else 0
        
        # Collect outputs (ensure all are strings)
        stdout_list = [str(tr.get('stdout', '')) for tr in results['test_results']]
        stderr_list = [str(tr.get('stderr', '')) for tr in results['test_results']]
        compile_output = str(results['test_results'][0].get('compile_output', '')) if results['test_results'] else ''
        
        # Update submission with results
        oa_client.update_submission(
            submission_id=submission_id,
            status='completed',
            score=score,
            passed_tests=passed_tests,
            total_tests=total_tests,
            execution_time=avg_time,
            memory_used=int(avg_memory),
            stdout='\n'.join(stdout_list),
            stderr='\n'.join(stderr_list),
            compile_output=compile_output,
            test_results=results
        )
        
        logger.info(
            f"Submission {submission_id} graded: "
            f"{passed_tests}/{total_tests} tests passed, score: {score}"
        )
        
        return {
            "success": True,
            "submission_id": submission_id,
            "score": score,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "all_passed": results['all_passed'],
            "execution_time": avg_time,
            "memory_used": int(avg_memory),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error grading submission {submission_id}: {str(e)}", exc_info=True)
        # Update submission with error status
        oa_client.update_submission(
            submission_id=submission_id,
            status='error',
            stderr=str(e)
        )
        return {
            "success": False,
            "error": str(e)
        }


def calculate_session_score(session_id: int) -> Dict[str, Any]:
    """
    Calculate overall score for an OA session based on all submissions
    
    Args:
        session_id: ID of the OA session
    
    Returns:
        Dictionary with session score details
    """
    try:
        # Get session
        session = oa_client.get_oa_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        # Get all questions in the session
        question_ids = session.get('QUESTION_IDS', [])
        if not question_ids:
            return {
                "success": False,
                "error": "No questions in session"
            }
        
        # Calculate max possible score
        max_score = 0
        for qid in question_ids:
            question = oa_client.get_question(qid)
            if question:
                max_score += float(question.get('POINTS', 100))
        
        # Get all submissions for this session
        submissions = oa_client.get_submissions_by_session(session_id)
        
        # Calculate best score for each question (in case of multiple attempts)
        question_scores = {}
        for sub in submissions:
            qid = sub['QUESTION_ID']
            score = float(sub.get('SCORE', 0) or 0)
            if qid not in question_scores or score > question_scores[qid]:
                question_scores[qid] = score
        
        # Total score is sum of best scores for each question
        total_score = sum(question_scores.values())
        
        return {
            "success": True,
            "session_id": session_id,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": (total_score / max_score * 100) if max_score > 0 else 0,
            "questions_attempted": len(question_scores),
            "total_questions": len(question_ids)
        }
        
    except Exception as e:
        logger.error(f"Error calculating session score for {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def complete_oa_session_with_results(session_id: int, max_cheating_score: Optional[float] = None) -> Dict[str, Any]:
    """
    Complete an OA session and update results to database
    Also updates the candidate's status in the main candidates table
    
    Args:
        session_id: ID of the OA session to complete
        max_cheating_score: Highest integrity/cheating score recorded during the session
    
    Returns:
        Dictionary with completion status and results
    """
    try:
        # Get session
        session = oa_client.get_oa_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        candidate_id = session['CANDIDATE_ID']
        
        # Calculate final session score
        score_result = calculate_session_score(session_id)
        if not score_result['success']:
            return score_result
        
        total_score = score_result['total_score']
        max_score = score_result['max_score']
        percentage = score_result['percentage']
        
        # Update OA session as completed
        oa_client.complete_oa_session(
            session_id=session_id,
            score=total_score,
            max_score=max_score,
            max_cheating_score=max_cheating_score
        )
        
        if max_cheating_score is not None:
            logger.info(
                f"✅ OA session {session_id} completed with max_cheating_score: {max_cheating_score}"
            )
        else:
            logger.warning(
                f"⚠️ OA session {session_id} completed without max_cheating_score (was None)"
            )
        
        # Update OA_RESULTS table
        oa_result = snowflake_client.get_oa_result(candidate_id)
        if oa_result:
            logger.info(f"📝 Updating existing OA result {oa_result['ID']} for candidate {candidate_id} with integrity_score: {max_cheating_score}")
            # Update existing OA result
            success = snowflake_client.update_oa_result(
                oa_id=oa_result['ID'],
                score=total_score,
                status='completed',
                completed_at=None,  # Will use CURRENT_TIMESTAMP
                integrity_score=max_cheating_score  # Save integrity score to oa_results table
            )
            if success:
                logger.info(f"✅ Successfully updated OA result {oa_result['ID']} with integrity_score: {max_cheating_score}")
            else:
                logger.error(f"❌ Failed to update OA result {oa_result['ID']}")
        else:
            logger.info(f"📝 Creating new OA result for candidate {candidate_id}")
            # Create new OA result if doesn't exist
            oa_result_id = snowflake_client.create_oa_result(
                candidate_id=candidate_id,
                status='completed'
            )
            logger.info(f"✅ Created OA result {oa_result_id}, now updating with integrity_score: {max_cheating_score}")
            success = snowflake_client.update_oa_result(
                oa_id=oa_result_id,
                score=total_score,
                status='completed',
                completed_at=None,
                integrity_score=max_cheating_score  # Save integrity score to oa_results table
            )
            if success:
                logger.info(f"✅ Successfully updated new OA result {oa_result_id} with integrity_score: {max_cheating_score}")
            else:
                logger.error(f"❌ Failed to update new OA result {oa_result_id}")
        
        # Update candidate stage based on OA performance
        # You can customize these thresholds
        if percentage >= 70:
            # Passed OA - move to next stage (oa_passed)
            snowflake_client.update_candidate_stage(candidate_id, 'oa_passed')
            logger.info(
                f"Candidate {candidate_id} passed OA with {percentage:.1f}% "
                f"({total_score}/{max_score})"
            )
        else:
            # Failed OA - keep at oa_sent or mark as failed
            logger.info(
                f"Candidate {candidate_id} did not pass OA threshold: {percentage:.1f}%"
            )
        
        # Get candidate info for logging
        candidate = snowflake_client.get_candidate(candidate_id)
        
        logger.info(
            f"OA session {session_id} completed for candidate {candidate_id} "
            f"({candidate.get('NAME', 'Unknown')}): "
            f"Score {total_score}/{max_score} ({percentage:.1f}%)"
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "candidate_id": candidate_id,
            "candidate_name": candidate.get('NAME'),
            "candidate_email": candidate.get('EMAIL'),
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "passed": percentage >= 70,
            "new_stage": 'oa_passed' if percentage >= 70 else 'oa_sent'
        }
        
    except Exception as e:
        logger.error(f"Error completing OA session {session_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_oa_results_for_candidate(candidate_id: int) -> Dict[str, Any]:
    """
    Get comprehensive OA results for a candidate
    
    Args:
        candidate_id: ID of the candidate
    
    Returns:
        Dictionary with all OA results
    """
    try:
        # Get candidate info
        candidate = snowflake_client.get_candidate(candidate_id)
        if not candidate:
            return {
                "success": False,
                "error": "Candidate not found"
            }
        
        # Get all OA sessions
        sessions = oa_client.get_sessions_by_candidate(candidate_id)
        
        # Get detailed results for each session
        session_details = []
        for session in sessions:
            session_id = session['ID']
            submissions = oa_client.get_submissions_by_session(session_id)
            
            session_details.append({
                "session_id": session_id,
                "status": session['STATUS'],
                "score": session.get('SCORE'),
                "max_score": session.get('MAX_SCORE'),
                "started_at": session.get('STARTED_AT'),
                "completed_at": session.get('COMPLETED_AT'),
                "duration_minutes": session.get('DURATION_MINUTES'),
                "total_submissions": len(submissions),
                "submissions": submissions
            })
        
        # Get stats
        stats = oa_client.get_candidate_oa_stats(candidate_id)
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "candidate_name": candidate.get('NAME'),
            "candidate_email": candidate.get('EMAIL'),
            "current_stage": candidate.get('STAGE'),
            "fit_score": candidate.get('FIT_SCORE'),
            "sessions": session_details,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting OA results for candidate {candidate_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def auto_grade_all_pending_submissions() -> Dict[str, Any]:
    """
    Batch grade all pending submissions (useful for cron jobs)
    
    Returns:
        Dictionary with batch grading results
    """
    try:
        # This would require a query to get all pending submissions
        # For now, return a placeholder
        logger.info("Auto-grading all pending submissions...")
        
        return {
            "success": True,
            "message": "Batch grading completed",
            "graded": 0,
            "failed": 0
        }
        
    except Exception as e:
        logger.error(f"Error in batch grading: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

