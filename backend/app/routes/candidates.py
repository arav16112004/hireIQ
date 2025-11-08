from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db import snowflake_client
from app.services import oa_trigger
from app.core.logger import logger

router = APIRouter(prefix="/candidates", tags=["Candidates"])


class SendOARequest(BaseModel):
    force: bool = False
    threshold: Optional[float] = None

@router.post("/{candidate_id}/evaluate")
def evaluate_candidate(candidate_id: int):
    candidate = snowflake_client.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Placeholder for AI evaluation
    return {
        "candidate_id": candidate_id,
        "message": "Evaluation endpoint - AI integration pending"
    }

@router.get("/{candidate_id}")
def get_candidate(candidate_id: int):
    candidate = snowflake_client.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/{candidate_id}/send-oa")
def send_oa_invitation(candidate_id: int, request: SendOARequest = None):
    """
    Send OA invitation email to a candidate
    
    Checks if candidate meets fit score threshold (default 0.7)
    and sends OA link if eligible.
    """
    try:
        # Get candidate to verify exists
        candidate = snowflake_client.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Trigger OA
        result = oa_trigger.trigger_oa_for_candidate(
            candidate_id=candidate_id,
            threshold=request.threshold if request else None,
            force=request.force if request else False
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to send OA invitation")
            )
        
        logger.info(f"OA invitation sent to candidate {candidate_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OA to candidate {candidate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}/email-logs")
def get_candidate_email_logs(candidate_id: int):
    """
    Get all email logs for a candidate
    """
    try:
        candidate = snowflake_client.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        logs = snowflake_client.get_email_logs_for_candidate(candidate_id)
        
        return {
            "candidate_id": candidate_id,
            "candidate_email": candidate.get("EMAIL"),
            "total_emails": len(logs),
            "logs": logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email logs for candidate {candidate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

