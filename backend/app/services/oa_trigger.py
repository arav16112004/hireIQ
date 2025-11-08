from typing import Optional
from app.core.config import settings
from app.db import snowflake_client
from app.core.logger import logger
from app.utils.email_utils import send_oa_email as send_oa_email_util


# Threshold for sending OA (default 0.7 = 70% fit score)
OA_THRESHOLD = settings.oa_threshold


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


def generate_oa_link(candidate_id: int, base_url: Optional[str] = None) -> str:
    """
    Generate a unique OA link for a candidate.
    
    Args:
        candidate_id: ID of the candidate
        base_url: Base URL for the OA platform (defaults to config)
    
    Returns:
        OA link URL
    """
    base_url = base_url or settings.oa_base_url
    # Generate secure token (in production, store this token in DB for validation)
    import secrets
    token = secrets.token_urlsafe(32)
    return f"{base_url}?candidate_id={candidate_id}&token={token}"


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
    force: bool = False
) -> dict:
    """
    Main function to trigger OA invitation for a candidate.
    
    Args:
        candidate_id: ID of the candidate
        threshold: Fit score threshold (optional)
        force: If True, send OA regardless of threshold (for testing)
    
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
        
        # Check if OA already sent
        existing_oa = snowflake_client.get_oa_result(candidate_id)
        if existing_oa and existing_oa.get("status") == "pending":
            return {
                "success": False,
                "error": "OA already sent to this candidate",
                "candidate_id": candidate_id,
                "oa_id": existing_oa.get("id")
            }
        
        # Get job info for personalization
        job = None
        if candidate.get("JOB_ID"):
            job = snowflake_client.get_job(candidate["JOB_ID"])
        
        # Generate OA link
        oa_link = generate_oa_link(candidate_id)
        
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
                "candidate_id": candidate_id
            }
        
        # Create OA result record
        oa_id = snowflake_client.create_oa_result(candidate_id, status="pending")
        
        # Update candidate stage
        snowflake_client.update_candidate_stage(candidate_id, "oa_sent")
        
        logger.info(
            f"OA triggered successfully for candidate {candidate_id}. "
            f"OA ID: {oa_id}, Link: {oa_link}"
        )
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "oa_id": oa_id,
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

