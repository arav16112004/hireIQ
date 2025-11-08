from fastapi import APIRouter, HTTPException
from app.db import snowflake_client

router = APIRouter(prefix="/candidates", tags=["Candidates"])

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

