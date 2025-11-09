from fastapi import APIRouter, UploadFile, Form, HTTPException, File, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.db import snowflake_client
from app.services import oa_trigger
from app.services.gemini_service import GeminiService
from app.core.logger import logger
from app.utils.auth_utils import get_current_user

# Import PyMuPDF (fitz) for PDF text extraction
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logger.warning("PyMuPDF (fitz) not installed. PDF processing will not work. Install with: pip install PyMuPDF")

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("/")
def get_all_candidates(
    job_id: Optional[int] = None,
    stage: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all candidates, optionally filtered by job_id and/or stage"""
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # If recruiter, only show candidates from their company
    if user_role in ["recruiter", "admin"]:
        user_data = snowflake_client.get_user_by_id(current_user.get("user_id"))
        if user_data:
            company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
            if company_name:
                candidates = snowflake_client.get_candidates_by_company(company_name)
                # Apply job_id and stage filters if provided
                if job_id:
                    candidates = [c for c in candidates if c.get("JOB_ID") == job_id or c.get("job_id") == job_id]
                if stage:
                    candidates = [c for c in candidates if (c.get("STAGE") or c.get("stage", "")).lower() == stage.lower()]
                return {"candidates": candidates}
    
    # For candidates or if no company found, return all candidates (or empty)
    candidates = snowflake_client.get_all_candidates(job_id=job_id, stage=stage)
    return {"candidates": candidates}


@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a candidate (recruiter/admin only)"""
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # Check if user is recruiter or admin
    if user_role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Only recruiters can delete candidates")
    
    # Verify candidate exists and belongs to recruiter's company (if recruiter)
    if user_role == "recruiter":
        candidate = snowflake_client.get_all_candidates()
        candidate_data = next((c for c in candidate if (c.get("ID") or c.get("id")) == candidate_id), None)
        if not candidate_data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Check if candidate belongs to recruiter's company
        user_data = snowflake_client.get_user_by_id(current_user.get("user_id"))
        if user_data:
            company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
            if company_name:
                # Get job for this candidate
                job_id = candidate_data.get("JOB_ID") or candidate_data.get("job_id")
                if job_id:
                    job = snowflake_client.get_job(job_id)
                    if job:
                        job_company = job.get("COMPANY_NAME") or job.get("company_name")
                        if job_company != company_name:
                            raise HTTPException(status_code=403, detail="Cannot delete candidate from another company")
    
    success = snowflake_client.delete_candidate(candidate_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete candidate")
    
    return {"message": "Candidate deleted successfully"}


class SendOARequest(BaseModel):
    force: bool = False
    threshold: Optional[float] = None


class CandidateResponse(BaseModel):
    candidate_id: Optional[int] = None
    fit_score: float
    skills: List[str]
    summary: Optional[str] = None
    status: str
    error: Optional[str] = None


class JobMatchRequest(BaseModel):
    skills: List[str]
    top_k: Optional[int] = 5


class JobMatch(BaseModel):
    job_id: int
    title: str
    score: float
    matching_skills: List[str]
    explanation: Optional[str] = None


class JobMatchResponse(BaseModel):
    matches: List[JobMatch]

@router.get("/test-gemini")
async def test_gemini():
    """Test if Gemini API is properly configured"""
    gemini = GeminiService()
    is_working = gemini.test_api_key()
    return {
        "status": "working" if is_working else "not_configured",
        "message": "Gemini API is responding" if is_working else "GEMINI_API_KEY not set or invalid"
    }


@router.post("/ingest", response_model=CandidateResponse)
async def ingest_candidate(
    file: UploadFile = File(...),
    job_id: int = Form(...),
    job_description: str = Form(""),
    name: str = Form(None),
    email: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Ingest a candidate resume (PDF) and analyze it using Gemini
    
    Uses authenticated user's email and name from JWT token.
    """
    # Always use authenticated user's info
    email = current_user.get("email")
    
    # Get name from users table
    user = snowflake_client.get_user_by_email(email)
    if user:
        name = user.get("NAME", "Candidate")
    else:
        name = "Candidate"
    
    logger.info(f"📝 Resume submission from authenticated user: {email}")
    logger.info(f"   Using name: {name}")
    logger.info(f"   Using email: {email}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # --- 1️⃣ Read resume text from PDF ---
    if fitz is None:
        return CandidateResponse(
            fit_score=0,
            skills=[],
            status="error",
            error="PyMuPDF is not installed. Please install it with: pip install PyMuPDF"
        )
    
    try:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        resume_text = ""
        for page in doc:
            resume_text += page.get_text("text")
        doc.close()
    except Exception as e:
        return CandidateResponse(
            fit_score=0,
            skills=[],
            status="error",
            error=f"Failed to read PDF: {str(e)}"
        )

    if not resume_text.strip():
        return CandidateResponse(
            fit_score=0,
            skills=[],
            status="error",
            error="PDF appears to be empty or unreadable"
        )

    # --- 2️⃣ Use Gemini to analyze resume ---
    try:
        gemini = GeminiService()
        result = gemini.extract_skills(resume_text, job_description)
        
        # Store experience info for each skill
        skills = result["skills"]
        fit_score = result["fit_score"]
        summary = result["summary"]
        experience_years = result.get("experience_years", {})
        
    except Exception as e:
        return CandidateResponse(
            fit_score=0,
            skills=[],
            status="error",
            error=f"Failed to analyze resume: {str(e)}"
        )

    # --- 3️⃣ Save to database ---
    try:
        logger.info(f"💾 Saving candidate to database:")
        logger.info(f"   Name: {name}")
        logger.info(f"   Email: {email}")
        logger.info(f"   Job ID: {job_id}")
        logger.info(f"   Resume: {file.filename}")
        
        candidate_id = snowflake_client.create_candidate(
            name=name,
            email=email,
            resume_url=f"uploads/{file.filename}",
            job_id=job_id
        )
        
        logger.info(f"✅ Candidate created with ID: {candidate_id}")
        
        # Save fit score
        snowflake_client.save_fit_score(candidate_id, fit_score, summary)
        
        # Determine status based on threshold
        status = "accepted" if fit_score >= 85 else "rejected"
        logger.info(f"Candidate {candidate_id} - Fit Score: {fit_score}% - Status: {status}")
        
        if fit_score < 85:
            snowflake_client.update_candidate_stage(candidate_id, "rejected")
            logger.info(f"Candidate {candidate_id} rejected (below 85% threshold)")
        else:
            logger.info(f"Candidate {candidate_id} accepted (>= 85% threshold) - Triggering OA automatically")
            
            # Automatically trigger OA for qualified candidates
            try:
                oa_result = oa_trigger.trigger_oa_for_candidate(candidate_id)
                if oa_result.get("success"):
                    logger.info(f"✅ OA automatically sent to {email}")
                else:
                    logger.error(f"❌ Failed to send OA: {oa_result.get('error')}")
            except Exception as e:
                logger.error(f"❌ Exception triggering OA: {str(e)}")
        
        return CandidateResponse(
            candidate_id=candidate_id,
            fit_score=fit_score,
            skills=skills,
            summary=summary,
            status="accepted"
        )
    except Exception as e:
        return CandidateResponse(
            fit_score=fit_score,
            skills=skills,
            summary=summary,
            status="error",
            error=f"Failed to save candidate: {str(e)}"
        )


@router.post("/{candidate_id}/evaluate")
def evaluate_candidate(candidate_id: int):
    """Evaluate a candidate (placeholder for AI evaluation)"""
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
    """Get candidate by ID"""
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


@router.post("/match", response_model=JobMatchResponse)
def match_jobs(candidate_id: int):
    """Match jobs based on candidate ID using AI-powered ranking"""
    # Get candidate and their extracted skills
    candidate = snowflake_client.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get all jobs to match against
    jobs = snowflake_client.get_all_jobs()
    
    # Try to get skills from candidate (may be stored in different formats)
    skills = []
    if candidate.get("SKILLS"):
        # Skills might be stored as a string, comma-separated, or JSON
        skills_str = candidate.get("SKILLS")
        if isinstance(skills_str, str):
            # Try to parse as JSON first
            try:
                import json
                skills = json.loads(skills_str)
            except:
                # If not JSON, split by comma
                skills = [s.strip() for s in skills_str.split(",") if s.strip()]
    
    # Use Gemini to rank jobs if we have skills
    if skills:
        try:
            gemini = GeminiService()
            ai_matches = gemini.rank_jobs(skills, jobs)
            # Convert to JobMatch format
            matches = [
                JobMatch(
                    job_id=match.get("job_id"),
                    title=next((j.get("title", "") for j in jobs if j.get("id") == match.get("job_id")), ""),
                    score=match.get("score", 0) / 100.0,  # Convert to 0-1 scale
                    matching_skills=match.get("matching_skills", [])
                )
                for match in ai_matches
            ]
            return JobMatchResponse(matches=matches)
        except Exception as e:
            logger.warning(f"AI job matching failed: {str(e)}, falling back to simple matching")
    
    # Fallback to simple matching
    matches = [
        JobMatch(
            job_id=job.get("id"),
            title=job.get("title", ""),
            score=0.5,
            matching_skills=[]
        )
        for job in jobs
    ]
    
    return JobMatchResponse(matches=matches)


@router.post("/match_by_skills", response_model=JobMatchResponse)
def match_jobs_by_skills(request: JobMatchRequest):
    """Match and rank jobs based on provided skills"""
    if not request.skills:
        raise HTTPException(status_code=400, detail="Skills list cannot be empty")
    
    jobs = snowflake_client.get_all_jobs()
    
    # Simple skill matching - score based on keyword matches
    matches = []
    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        matching_skills = [skill for skill in request.skills if skill.lower() in job_text]
        score = len(matching_skills) / len(request.skills) if request.skills else 0
        
        matches.append(JobMatch(
            job_id=job.get("id"),
            title=job.get("title", ""),
            score=score,
            matching_skills=matching_skills
        ))
    
    matches.sort(key=lambda x: x.score, reverse=True)
    
    # Limit to top_k results if specified
    if request.top_k:
        matches = matches[:request.top_k]
    
    return JobMatchResponse(matches=matches)

