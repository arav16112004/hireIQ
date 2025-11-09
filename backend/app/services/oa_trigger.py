from typing import Optional
from app.core.config import settings
from app.db import snowflake_client, oa_client
from app.core.logger import logger
from app.utils.email_utils import send_oa_email as send_oa_email_util


# Threshold for sending OA (default 0.7 = 70% fit score)
OA_THRESHOLD = settings.oa_threshold

# Default OA configuration
DEFAULT_OA_DURATION = 60  # minutes
DEFAULT_OA_QUESTIONS = [1, 2]  # Default question IDs (make sure these exist in DB)


def check_candidate_qualifies(candidate_id: int, threshold: Optional[float] = None) -> bool:
    """
    Check if a candidate qualifies for OA based on fit score.
    
    Args:
        candidate_id: ID of the candidate
        threshold: Fit score threshold (defaults to OA_THRESHOLD)
    
    Returns:
        True if candidate qualifies, False otherwise
    """
    threshold = threshold or OA_THRESHOLD
    
    candidate = snowflake_client.get_candidate(candidate_id)
    if not candidate:
        logger.warning(f"Candidate {candidate_id} not found")
        return False
    
    fit_score = candidate.get("FIT_SCORE")
    if fit_score is None:
        logger.info(f"Candidate {candidate_id} has no fit score yet")
        return False
    
    # Convert to float
    fit_score = float(fit_score)
    
    # Normalize threshold to same scale as fit_score (both out of 100)
    threshold_normalized = threshold * 100 if threshold <= 1.0 else threshold
    
    # Check if candidate already has OA sent
    if candidate.get("STAGE") == "oa_sent":
        logger.info(f"Candidate {candidate_id} already has OA sent")
        return False
    
    qualifies = fit_score >= threshold_normalized
    logger.info(
        f"Candidate {candidate_id} fit_score: {fit_score}, "
        f"threshold: {threshold}, qualifies: {qualifies}"
    )
    return qualifies


def create_oa_session_for_candidate(
    candidate_id: int,
    question_ids: Optional[list] = None,
    duration_minutes: int = DEFAULT_OA_DURATION
) -> int:
    """
    Create an OA session for a candidate
    
    Args:
        candidate_id: ID of the candidate
        question_ids: List of question IDs (defaults to DEFAULT_OA_QUESTIONS)
        duration_minutes: Duration in minutes
        
    Returns:
        session_id: Created session ID
    """
    question_ids = question_ids or DEFAULT_OA_QUESTIONS
    
    # Create OA session
    session_id = oa_client.create_oa_session(
        candidate_id=candidate_id,
        question_ids=question_ids,
        duration_minutes=duration_minutes
    )
    
    logger.info(f"Created OA session {session_id} for candidate {candidate_id}")
    return session_id


def generate_oa_link(
    session_id: int,
    candidate_id: int,
    base_url: Optional[str] = None
) -> str:
    """
    Generate a unique OA link for a candidate session.
    
    Args:
        session_id: OA session ID
        candidate_id: ID of the candidate
        base_url: Base URL for the OA platform (defaults to config)
    
    Returns:
        OA link URL
    """
    # Import here to avoid circular dependency
    from app.routes.oa import get_oa_link
    
    base_url = base_url or settings.oa_base_url or "http://localhost:3000"
    # Ensure base_url doesn't have /oa/ at the end (get_oa_link will add it)
    base_url = base_url.rstrip('/')
    if base_url.endswith('/oa'):
        base_url = base_url[:-3]
    return get_oa_link(session_id, candidate_id, base_url)


def send_oa_email(
    candidate_email: str,
    candidate_name: str,
    oa_link: str,
    job_title: Optional[str] = None
) -> bool:
    """
    Send OA invitation email via SendGrid.
    
    Args:
        candidate_email: Email address of the candidate
        candidate_name: Name of the candidate
        oa_link: Link to the OA platform
        job_title: Optional job title for personalization (unused, kept for compatibility)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Use the centralized email utility
    return send_oa_email_util(
        to_email=candidate_email,
        candidate_name=candidate_name,
        oa_link=oa_link,
        company_name="SeroHire"
    )


def trigger_oa_for_candidate(
    candidate_id: int,
    threshold: Optional[float] = None,
    force: bool = False,
    question_ids: Optional[list] = None,
    duration_minutes: int = DEFAULT_OA_DURATION
) -> dict:
    """
    Main function to trigger OA invitation for a candidate.
    
    Args:
        candidate_id: ID of the candidate
        threshold: Fit score threshold (optional)
        force: If True, send OA regardless of threshold (for testing)
        question_ids: List of question IDs for the OA (optional)
        duration_minutes: OA duration in minutes
    
    Returns:
        Dictionary with status and details
    """
    try:
        # Get candidate info
        candidate = snowflake_client.get_candidate(candidate_id)
        if not candidate:
            return {
                "success": False,
                "error": "Candidate not found",
                "candidate_id": candidate_id
            }
        
        # Check if candidate qualifies (unless forced)
        if not force:
            if not check_candidate_qualifies(candidate_id, threshold):
                return {
                    "success": False,
                    "error": "Candidate does not meet threshold criteria",
                    "candidate_id": candidate_id,
                    "fit_score": candidate.get("FIT_SCORE"),
                    "threshold": threshold or OA_THRESHOLD
                }
        
        # Check if OA session already exists
        # Note: We'll allow creating new sessions if previous ones expired/completed
        
        # Get job info for personalization
        job = None
        if candidate.get("JOB_ID"):
            job = snowflake_client.get_job(candidate["JOB_ID"])
        
        # Create OA session
        session_id = create_oa_session_for_candidate(
            candidate_id=candidate_id,
            question_ids=question_ids,
            duration_minutes=duration_minutes
        )
        
        # Generate OA link with token
        oa_link = generate_oa_link(session_id, candidate_id)
        
        # Send email
        email_sent = send_oa_email(
            candidate_email=candidate["EMAIL"],
            candidate_name=candidate["NAME"],
            oa_link=oa_link,
            job_title=job.get("TITLE") if job else None
        )
        
        # Log email attempt
        email_status = 'sent' if email_sent else 'failed'
        error_msg = None if email_sent else "Failed to send via SendGrid"
        
        snowflake_client.log_oa_email_sent(
            candidate_id=candidate_id,
            email=candidate["EMAIL"],
            oa_link=oa_link,
            status=email_status,
            error_message=error_msg
        )
        
        if not email_sent:
            return {
                "success": False,
                "error": "Failed to send OA email",
                "candidate_id": candidate_id,
                "session_id": session_id
            }
        
        # Update candidate stage
        snowflake_client.update_candidate_stage(candidate_id, "oa_sent")
        
        logger.info(
            f"OA triggered successfully for candidate {candidate_id}. "
            f"Session ID: {session_id}, Link: {oa_link}"
        )
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "session_id": session_id,
            "oa_link": oa_link,
            "email_sent": True
        }
        
    except Exception as e:
        logger.error(f"Error triggering OA for candidate {candidate_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "candidate_id": candidate_id
        }


def trigger_oa_for_qualified_candidates(
    job_id: Optional[int] = None,
    threshold: Optional[float] = None
) -> dict:
    """
    Trigger OA for all qualified candidates (batch processing).
    
    Args:
        job_id: Optional job ID to filter candidates
        threshold: Fit score threshold
    
    Returns:
        Dictionary with batch processing results
    """
    try:
        # Get candidates
        if job_id:
            candidates = snowflake_client.get_candidates_by_job(job_id)
        else:
            # Get all candidates (you might want to add a function for this)
            candidates = []
            logger.warning("Getting all candidates not implemented. Use job_id filter.")
            return {
                "success": False,
                "error": "Getting all candidates requires job_id"
            }
        
        results = {
            "total_candidates": len(candidates),
            "qualified": 0,
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        for candidate in candidates:
            candidate_id = candidate["id"]
            
            # Check if qualifies
            if check_candidate_qualifies(candidate_id, threshold):
                results["qualified"] += 1
                
                # Trigger OA
                result = trigger_oa_for_candidate(candidate_id, threshold)
                
                if result["success"]:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append({
                    "candidate_id": candidate_id,
                    "result": result
                })
        
        logger.info(
            f"Batch OA trigger completed: {results['sent']} sent, "
            f"{results['failed']} failed out of {results['total_candidates']} candidates"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error in batch OA trigger: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

