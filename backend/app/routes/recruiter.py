from fastapi import APIRouter, Depends, HTTPException
from app.db import snowflake_client, oa_client
from app.utils.auth_utils import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])

@router.get("/candidates")
def get_company_candidates(current_user: dict = Depends(get_current_user)):
    """Get all candidates for jobs under the recruiter's company"""
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # Check if user is recruiter or admin
    if user_role not in ["recruiter", "admin"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Only recruiters can access this endpoint. Your role: {current_user.get('role', 'unknown')}"
        )
    
    # Get user's company_name
    user_data = snowflake_client.get_user_by_id(current_user.get("user_id"))
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
    if not company_name:
        raise HTTPException(status_code=400, detail="Recruiter does not have a company assigned")
    
    # Get candidates for this company
    candidates = snowflake_client.get_candidates_by_company(company_name)
    
    # Enrich each candidate with OA session summary (max cheating score and OA score)
    enriched_candidates = []
    for candidate in candidates:
        candidate_id = candidate.get("ID") or candidate.get("id")
        if candidate_id:
            # Get OA results (has integrity_score column)
            oa_result = snowflake_client.get_oa_result(candidate_id)
            
            # Get OA sessions for this candidate
            oa_sessions = oa_client.get_sessions_by_candidate(candidate_id)
            
            # Extract max cheating score and OA score
            # Priority: 1) oa_results.integrity_score, 2) oa_sessions.max_cheating_score
            max_cheating_score = None
            oa_score = None
            oa_percentage = None
            has_completed_oa = False
            
            # First, try to get integrity_score from oa_results table
            if oa_result:
                integrity_score_from_results = oa_result.get("INTEGRITY_SCORE") or oa_result.get("integrity_score")
                if integrity_score_from_results is not None:
                    max_cheating_score = float(integrity_score_from_results)
            
            if oa_sessions:
                completed_sessions = [s for s in oa_sessions if s.get("STATUS") == "completed" or s.get("STATUS") == "COMPLETED"]
                if completed_sessions:
                    has_completed_oa = True
                    latest_session = completed_sessions[0]
                    oa_score = latest_session.get("SCORE") or latest_session.get("score")
                    oa_max_score = latest_session.get("MAX_SCORE") or latest_session.get("max_score")
                    
                    if oa_score is not None and oa_max_score is not None and oa_max_score > 0:
                        oa_percentage = (oa_score / oa_max_score) * 100
                    
                    # If we don't have integrity_score from oa_results, get it from sessions
                    if max_cheating_score is None:
                        cheating_scores = []
                        for session in completed_sessions:
                            score = session.get("MAX_CHEATING_SCORE") or session.get("max_cheating_score")
                            if score is not None:
                                cheating_scores.append(float(score))
                        
                        if cheating_scores:
                            max_cheating_score = max(cheating_scores)
            
            # Add OA summary to candidate
            candidate["max_cheating_score"] = max_cheating_score
            candidate["oa_score"] = oa_score
            candidate["oa_percentage"] = oa_percentage
            candidate["has_completed_oa"] = has_completed_oa
        
        enriched_candidates.append(candidate)
    
    return {
        "company_name": company_name,
        "candidates": enriched_candidates,
        "total": len(enriched_candidates)
    }


@router.get("/candidates/{candidate_id}")
def get_candidate_details(candidate_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get comprehensive candidate details including profile and OA session data
    
    Returns:
    - Candidate basic info (from CANDIDATES table)
    - Candidate profile (from CANDIDATE_PROFILES table)
    - OA sessions with scores and cheating scores
    """
    # Check if user is recruiter or admin
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    if user_role not in ["recruiter", "admin"]:
        raise HTTPException(
            status_code=403,
            detail=f"Only recruiters can access this endpoint. Your role: {current_user.get('role', 'unknown')}"
        )
    
    # Get candidate basic info
    candidate = snowflake_client.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get candidate profile (from candidate_profiles table)
    # Note: USER_ID in candidate_profiles references CANDIDATES(id), so we use candidate_id directly
    profile = snowflake_client.get_candidate_profile_by_candidate_id(candidate_id)
    
    # Get OA sessions for this candidate
    oa_sessions = oa_client.get_sessions_by_candidate(candidate_id)
    
    # Get OA results (this table has integrity_score column)
    oa_result = snowflake_client.get_oa_result(candidate_id)
    
    # Get job info if available
    job = None
    if candidate.get("JOB_ID"):
        job = snowflake_client.get_job(candidate.get("JOB_ID"))
    
    # Build response
    response = {
        "candidate": candidate,
        "profile": profile,
        "oa_sessions": oa_sessions,
        "oa_result": oa_result,
        "job": job
    }
    
    # Extract max cheating score and OA score
    # Priority: 1) oa_results.integrity_score, 2) oa_sessions.max_cheating_score
    max_cheating_score = None
    oa_score = None
    oa_max_score = None
    oa_percentage = None
    
    # First, try to get integrity_score from oa_results table
    if oa_result:
        integrity_score_from_results = oa_result.get("INTEGRITY_SCORE") or oa_result.get("integrity_score")
        logger.info(f"📊 OA result for candidate {candidate_id}: integrity_score={integrity_score_from_results}, oa_result keys: {list(oa_result.keys())}")
        if integrity_score_from_results is not None:
            max_cheating_score = float(integrity_score_from_results)
            logger.info(f"✅ Using integrity_score from oa_results: {max_cheating_score}")
        else:
            logger.warning(f"⚠️ OA result exists but integrity_score is None for candidate {candidate_id}")
    
    # Also check oa_sessions for max_cheating_score (fallback or if oa_results doesn't have it)
    if oa_sessions:
        # Find completed sessions and get highest cheating score across all sessions
        completed_sessions = [s for s in oa_sessions if s.get("STATUS") == "completed" or s.get("STATUS") == "COMPLETED"]
        if completed_sessions:
            # Get the most recent completed session for OA score
            latest_session = completed_sessions[0]
            oa_score = latest_session.get("SCORE") or latest_session.get("score")
            oa_max_score = latest_session.get("MAX_SCORE") or latest_session.get("max_score")
            if oa_score is not None and oa_max_score is not None and oa_max_score > 0:
                oa_percentage = (oa_score / oa_max_score) * 100
            
            # If we don't have integrity_score from oa_results, get it from sessions
            if max_cheating_score is None:
                cheating_scores = []
                for session in completed_sessions:
                    score = session.get("MAX_CHEATING_SCORE") or session.get("max_cheating_score")
                    if score is not None:
                        cheating_scores.append(float(score))
                
                if cheating_scores:
                    max_cheating_score = max(cheating_scores)
                    logger.info(f"Using max_cheating_score from oa_sessions: {max_cheating_score}")
    
    response["max_cheating_score"] = max_cheating_score
    response["oa_score"] = oa_score
    response["oa_max_score"] = oa_max_score
    response["oa_percentage"] = oa_percentage
    
    return response