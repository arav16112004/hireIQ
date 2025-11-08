from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
from app.db import snowflake_client
from app.core.logger import logger


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
    
    fit_score = candidate.get("fit_score")
    if fit_score is None:
        logger.info(f"Candidate {candidate_id} has no fit score yet")
        return False
    
    # Check if candidate already has OA sent
    if candidate.get("stage") == "oa_sent":
        logger.info(f"Candidate {candidate_id} already has OA sent")
        return False
    
    qualifies = fit_score >= threshold
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
        job_title: Optional job title for personalization
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.sendgrid_api_key:
        logger.error("SendGrid API key not configured")
        return False
    
    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        
        from_email = Email(settings.sendgrid_from_email)
        to_email = To(candidate_email)
        
        subject = f"Online Assessment Invitation - {job_title or 'TeamSero'}"
        
        # Email template
        html_content = f"""
        <html>
            <body>
                <h2>Congratulations, {candidate_name}!</h2>
                <p>Thank you for your interest in joining our team. Based on your application, 
                we'd like to invite you to complete an online assessment.</p>
                
                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Click the link below to access your online assessment</li>
                    <li>Complete the assessment at your convenience</li>
                    <li>You'll hear from us shortly after completion</li>
                </ol>
                
                <p>
                    <a href="{oa_link}" style="background-color: #4CAF50; color: white; 
                    padding: 14px 28px; text-decoration: none; display: inline-block; 
                    border-radius: 4px; font-weight: bold;">
                        Start Assessment
                    </a>
                </p>
                
                <p>Or copy and paste this link into your browser:<br>
                <a href="{oa_link}">{oa_link}</a></p>
                
                <p>This link is unique to you and will expire in 7 days.</p>
                
                <p>Best regards,<br>The TeamSero Hiring Team</p>
            </body>
        </html>
        """
        
        text_content = f"""
        Congratulations, {candidate_name}!
        
        Thank you for your interest in joining our team. Based on your application, 
        we'd like to invite you to complete an online assessment.
        
        Next Steps:
        1. Click the link below to access your online assessment
        2. Complete the assessment at your convenience
        3. You'll hear from us shortly after completion
        
        Start your assessment here: {oa_link}
        
        This link is unique to you and will expire in 7 days.
        
        Best regards,
        The TeamSero Hiring Team
        """
        
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=Content("text/html", html_content),
            plain_text_content=Content("text/plain", text_content)
        )
        
        response = sg.send(message)
        
        if response.status_code in [200, 202]:
            logger.info(f"OA email sent successfully to {candidate_email}")
            return True
        else:
            logger.error(
                f"Failed to send OA email to {candidate_email}. "
                f"Status code: {response.status_code}"
            )
            return False
            
    except Exception as e:
        logger.error(f"Error sending OA email to {candidate_email}: {str(e)}")
        return False


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
                    "fit_score": candidate.get("fit_score"),
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
        if candidate.get("job_id"):
            job = snowflake_client.get_job(candidate["job_id"])
        
        # Generate OA link
        oa_link = generate_oa_link(candidate_id)
        
        # Send email
        email_sent = send_oa_email(
            candidate_email=candidate["email"],
            candidate_name=candidate["name"],
            oa_link=oa_link,
            job_title=job.get("title") if job else None
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

