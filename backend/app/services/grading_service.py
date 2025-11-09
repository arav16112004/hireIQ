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
    Calculate overall score for an OA session.
    Priority: 1) Use session's SCORE/MAX_SCORE if set, 2) Calculate from submissions
    
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
        
        # Priority 1: Check if session already has SCORE and MAX_SCORE set
        # Handle case-insensitive column names (Snowflake might return uppercase)
        session_score = None
        session_max_score = None
        session_status = None
        
        # Try multiple case variations
        for key in session.keys():
            key_upper = key.upper()
            if key_upper == 'SCORE':
                session_score = session[key]
            elif key_upper == 'MAX_SCORE':
                session_max_score = session[key]
            elif key_upper == 'STATUS':
                session_status = session[key]
        
        # Also try direct access
        if session_score is None:
            session_score = session.get('SCORE') or session.get('score') or session.get('Score')
        if session_max_score is None:
            session_max_score = session.get('MAX_SCORE') or session.get('max_score') or session.get('Max_Score')
        if session_status is None:
            session_status = session.get('STATUS') or session.get('status') or session.get('Status')
        
        logger.info(f"Session {session_id} raw data: {list(session.keys())}")
        logger.info(f"Session {session_id}: score={session_score}, max_score={session_max_score}, status={session_status}")
        
        if session_score is not None and session_max_score is not None:
            try:
                score_float = float(session_score)
                max_score_float = float(session_max_score)
                
                logger.info(f"Parsed scores: score_float={score_float}, max_score_float={max_score_float}")
                
                if max_score_float > 0:
                    percentage = (score_float / max_score_float) * 100
                    logger.info(f"✅ Using session SCORE/MAX_SCORE: {score_float}/{max_score_float} = {percentage:.2f}%")
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "total_score": score_float,
                        "max_score": max_score_float,
                        "percentage": percentage,
                        "questions_attempted": len(question_ids),  # Assume all questions attempted if score is set
                        "total_questions": len(question_ids),
                        "source": "session_scores"
                    }
                else:
                    logger.warning(f"max_score_float is 0 or negative: {max_score_float}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing session scores: {e}, falling back to submission calculation")
                logger.warning(f"session_score type: {type(session_score)}, value: {session_score}")
                logger.warning(f"session_max_score type: {type(session_max_score)}, value: {session_max_score}")
        else:
            logger.warning(f"Session {session_id} missing SCORE or MAX_SCORE: score={session_score}, max_score={session_max_score}")
        
        # Priority 2: Calculate from submissions
        logger.info(f"Session doesn't have SCORE/MAX_SCORE, calculating from submissions...")
        
        # Calculate max possible score
        max_score = 0
        for qid in question_ids:
            question = oa_client.get_question(qid)
            if question:
                max_score += float(question.get('POINTS', 100))
        
        # Get all submissions for this session
        submissions = oa_client.get_submissions_by_session(session_id)
        logger.info(f"Found {len(submissions)} submission(s) for session {session_id}")
        
        # Calculate best score for each question (in case of multiple attempts)
        question_scores = {}
        for sub in submissions:
            qid = sub.get('QUESTION_ID')
            if qid:
                try:
                    score = float(sub.get('SCORE', 0) or 0)
                    if qid not in question_scores or score > question_scores[qid]:
                        question_scores[qid] = score
                        logger.info(f"Question {qid}: best score = {score}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing score for submission {sub.get('ID')}: {e}")
        
        # Total score is sum of best scores for each question
        total_score = sum(question_scores.values())
        logger.info(f"Calculated from submissions: total_score={total_score}, max_score={max_score}")
        
        return {
            "success": True,
            "session_id": session_id,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": (total_score / max_score * 100) if max_score > 0 else 0,
            "questions_attempted": len(question_scores),
            "total_questions": len(question_ids),
            "source": "submissions"
        }
        
    except Exception as e:
        logger.error(f"Error calculating session score for {session_id}: {str(e)}", exc_info=True)
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


def get_best_oa_score_percentage(candidate_id: int) -> Optional[float]:
    """
    Get the best OA score percentage for a candidate.
    Priority: 1) OA_SESSIONS table (most reliable - has both score and max_score), 2) OA_RESULTS table
    
    Args:
        candidate_id: ID of the candidate
    
    Returns:
        Best percentage score (0-100) or None if no completed OA assessments
    """
    try:
        best_percentage = None
        logger.info(f"🔍 Checking OA scores for candidate {candidate_id}")
        
        # Priority 1: Check OA_SESSIONS table for completed sessions (calculate percentage)
        # This is more reliable because it has both SCORE and MAX_SCORE
        sessions = oa_client.get_sessions_by_candidate(candidate_id)
        logger.info(f"Found {len(sessions)} OA session(s) for candidate {candidate_id}")
        
        for session in sessions:
            # Handle case-insensitive column names
            session_id = session.get('ID') or session.get('id') or session.get('Id')
            status = None
            score = None
            max_score = None
            
            # Try multiple case variations
            for key in session.keys():
                key_upper = key.upper()
                if key_upper == 'STATUS':
                    status = session[key]
                elif key_upper == 'SCORE':
                    score = session[key]
                elif key_upper == 'MAX_SCORE':
                    max_score = session[key]
            
            # Fallback to direct access
            if status is None:
                status = session.get('STATUS') or session.get('status') or session.get('Status')
            if score is None:
                score = session.get('SCORE') or session.get('score') or session.get('Score')
            if max_score is None:
                max_score = session.get('MAX_SCORE') or session.get('max_score') or session.get('Max_Score')
            
            logger.info(f"Session {session_id}: status={status}, score={score}, max_score={max_score} (raw keys: {list(session.keys())[:5]}...)")
            
            # Check if session is completed (case-insensitive)
            if status:
                status_upper = str(status).upper().strip()
                if status_upper in ('COMPLETED', 'COMPLETE'):
                    # Try to get score from session SCORE/MAX_SCORE first
                    if score is not None and max_score is not None:
                        try:
                            score_float = float(score)
                            max_score_float = float(max_score)
                            
                            logger.info(f"Session {session_id}: score_float={score_float}, max_score_float={max_score_float}")
                            
                            if max_score_float > 0:
                                percentage = (score_float / max_score_float) * 100
                                logger.info(f"Session {session_id}: calculated percentage = {percentage:.2f}%")
                                
                                if best_percentage is None or percentage > best_percentage:
                                    best_percentage = percentage
                                    logger.info(f"✅ New best score: {best_percentage:.2f}% from session {session_id}")
                            else:
                                logger.warning(f"Session {session_id}: max_score_float is 0 or negative: {max_score_float}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error calculating percentage for session {session_id}: {e}")
                            logger.warning(f"  score type: {type(score)}, value: {score}")
                            logger.warning(f"  max_score type: {type(max_score)}, value: {max_score}")
                    else:
                        logger.warning(f"Session {session_id} is completed but missing score or max_score: score={score}, max_score={max_score}")
                        # Fallback: Calculate score from submissions for this session
                        logger.info(f"Attempting to calculate score from submissions for session {session_id}...")
                        try:
                            session_score_result = calculate_session_score(session_id)
                            if session_score_result.get('success') and session_score_result.get('percentage') is not None:
                                session_percentage = session_score_result['percentage']
                                logger.info(f"Calculated percentage from submissions for session {session_id}: {session_percentage:.2f}%")
                                if best_percentage is None or session_percentage > best_percentage:
                                    best_percentage = session_percentage
                                    logger.info(f"✅ New best score from submissions: {best_percentage:.2f}% from session {session_id}")
                        except Exception as e:
                            logger.warning(f"Failed to calculate score from submissions for session {session_id}: {e}")
                else:
                    logger.info(f"Session {session_id} status is '{status}' (not completed, expected 'completed')")
            else:
                logger.warning(f"Session {session_id} has no status field")
        
        # Priority 2: Check OA_RESULTS table as fallback (if no session data found)
        if best_percentage is None:
            logger.info(f"No completed sessions found, checking OA_RESULTS table...")
            oa_result = snowflake_client.get_oa_result(candidate_id)
            if oa_result:
                result_score = oa_result.get('SCORE') or oa_result.get('score')
                result_status = oa_result.get('STATUS') or oa_result.get('status')
                
                logger.info(f"OA_RESULTS: score={result_score}, status={result_status}")
                
                if result_score is not None and result_status and result_status.upper() == 'COMPLETED':
                    try:
                        score_float = float(result_score)
                        # OA_RESULTS score should be percentage (0-100) based on schema
                        # But if it's > 100, it might be a raw score
                        if score_float <= 100:
                            best_percentage = score_float
                            logger.info(f"✅ Found OA result percentage from OA_RESULTS: {best_percentage}%")
                        else:
                            logger.warning(f"OA_RESULTS score {score_float} is > 100, treating as raw score (not percentage)")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error parsing OA_RESULTS score: {e}")
        
        if best_percentage is not None:
            logger.info(f"✅ Best OA score for candidate {candidate_id}: {best_percentage:.2f}%")
        else:
            logger.warning(f"❌ No completed OA assessments found for candidate {candidate_id}")
        
        return best_percentage
        
    except Exception as e:
        logger.error(f"Error getting best OA score for candidate {candidate_id}: {str(e)}", exc_info=True)
        return None


def check_interview_eligibility(candidate_id: int, threshold: float = 90.0) -> Dict[str, Any]:
    """
    Check if a candidate is eligible for interview based on OA score
    
    Args:
        candidate_id: ID of the candidate
        threshold: Minimum OA score percentage required (default 90%)
    
    Returns:
        Dictionary with eligibility status and details
    """
    try:
        logger.info(f"🎯 Checking interview eligibility for candidate {candidate_id} (threshold: {threshold}%)")
        
        # Get best OA score
        best_score = get_best_oa_score_percentage(candidate_id)
        
        if best_score is None:
            logger.warning(f"❌ No OA score found for candidate {candidate_id}")
            return {
                "eligible": False,
                "reason": "No completed OA assessments found",
                "best_score": None,
                "threshold": threshold
            }
        
        # Use >= to allow exactly 90% to pass (or > for strictly above)
        eligible = best_score >= threshold
        
        logger.info(f"{'✅' if eligible else '❌'} Candidate {candidate_id}: score={best_score:.2f}%, threshold={threshold}%, eligible={eligible}")
        
        return {
            "eligible": eligible,
            "reason": "Eligible for interview" if eligible else f"OA score {best_score:.1f}% is below the required {threshold}%",
            "best_score": best_score,
            "threshold": threshold
        }
        
    except Exception as e:
        logger.error(f"Error checking interview eligibility for candidate {candidate_id}: {str(e)}", exc_info=True)
        return {
            "eligible": False,
            "reason": f"Error checking eligibility: {str(e)}",
            "best_score": None,
            "threshold": threshold
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

