from app.db import snowflake_client as db
from app.services.gemini_service import GeminiService
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.utils.auth_utils import get_current_user, get_optional_user


class JobMatchRequest(BaseModel):
    skills: List[str]
    top_k: Optional[int] = 5


class JobMatch(BaseModel):
    job_id: int
    title: str
    score: float
    matching_skills: List[str]


class JobMatchResponse(BaseModel):
    matches: List[JobMatch]


class CreateJobRequest(BaseModel):
    title: str
    description: str
    department: str
    company_principles: Optional[str] = None  # Company principles for AI avatar video interviews


class UpdateJobRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    company_principles: Optional[str] = None  # Company principles for AI avatar video interviews


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/")
def get_all_jobs(current_user: Optional[dict] = Depends(get_optional_user)):
    """Get all jobs. If recruiter (authenticated), only show jobs from their company."""
    # If no user or user is candidate, return all jobs
    if not current_user:
        jobs = db.get_all_jobs()
        return {"jobs": jobs}
    
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # If recruiter or admin, filter by company
    if user_role in ["recruiter", "admin"]:
        user_data = db.get_user_by_id(current_user.get("user_id"))
        if user_data:
            company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
            if company_name:
                jobs = db.get_jobs_by_company(company_name)
                return {"jobs": jobs}
    
    # For candidates or if no company found, return all jobs
    jobs = db.get_all_jobs()
    return {"jobs": jobs}


def _score_job_by_skills(job: dict, skills: List[str]) -> JobMatch:
    """Score a job based on direct skill matches."""
    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    matching = [skill for skill in skills if skill.lower() in job_text]
    score = len(matching) / len(skills) if skills else 0

    return JobMatch(
        job_id=job.get('id'),
        title=job.get('title', ''),
        score=score,
        matching_skills=matching
    )


@router.post("/match")
def match_jobs(candidate_id: int):
    """Match jobs based on candidate ID (simple lookup)."""
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    jobs = db.get_all_jobs()
    return {"matches": jobs}


@router.post("/match_by_skills", response_model=JobMatchResponse)
def match_jobs_by_skills(request: JobMatchRequest):
    """Match and rank jobs based on provided skills."""
    if not request.skills:
        raise HTTPException(status_code=400, detail="Skills list cannot be empty")

    jobs = db.get_all_jobs()
    matches = [_score_job_by_skills(job, request.skills) for job in jobs]
    matches.sort(key=lambda x: x.score, reverse=True)

    return JobMatchResponse(matches=matches[:request.top_k])


# -------------------------------------------------------------------------
# 🧠 AI-Powered Matching using Gemini
# -------------------------------------------------------------------------
@router.post("/match_ai")
def match_jobs_ai(candidate_id: int):
    """
    Match jobs using Gemini AI.
    Compares the candidate's resume (from DB) against all job descriptions.
    """
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    resume_text = candidate.get("resume_text") or ""
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Candidate resume text is empty")

    jobs = db.get_all_jobs()
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found in database")

    gemini = GeminiService()
    ai_matches = []

    for job in jobs:
        job_title = job.get("title", "Untitled Job")
        job_desc = job.get("description", "")

        print(f"[DEBUG] Analyzing job: {job_title}")

        try:
            result = gemini.extract_skills(resume_text, job_desc)
            fit_score = float(result.get("fit_score", 0))
            skills = result.get("skills", [])
            summary = result.get("summary", "")

            ai_matches.append({
                "job_id": job.get("id"),
                "title": job_title,
                "fit_score": fit_score,
                "skills": skills,
                "summary": summary
            })

        except Exception as e:
            print(f"[DEBUG] Gemini analysis failed for job '{job_title}': {str(e)}")
            ai_matches.append({
                "job_id": job.get("id"),
                "title": job_title,
                "fit_score": 0,
                "skills": [],
                "summary": f"Error analyzing job: {str(e)}"
            })

    ai_matches.sort(key=lambda x: x["fit_score"], reverse=True)
    return {"matches": ai_matches}


@router.get("/{job_id}")
def get_job(job_id: int):
    """Get a job by ID"""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/candidates")
def get_job_candidates(job_id: int):
    """Get all candidates for a specific job"""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidates = db.get_candidates_by_job(job_id)
    return {"job_id": job_id, "candidates": candidates}


@router.post("/")
def create_job(request: CreateJobRequest, current_user: dict = Depends(get_current_user)):
    """Create a new job (recruiter only)"""
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # Check if user is recruiter or admin
    if user_role not in ["recruiter", "admin"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Only recruiters can create jobs. Your role: {current_user.get('role', 'unknown')}"
        )
    
    # Get user's company_name if recruiter
    company_name = None
    if user_role == "recruiter":
        user_data = db.get_user_by_id(current_user.get("user_id"))
        if user_data:
            company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
            if not company_name:
                raise HTTPException(
                    status_code=400, 
                    detail="Recruiter account does not have a company assigned. Please contact admin."
                )
    elif user_role == "admin":
        # Admin can optionally set company_name, but it's not required
        # For now, admins create jobs without company_name
        pass
    
    try:
        job_id = db.create_job(
            title=request.title,
            description=request.description,
            department=request.department,
            company_name=company_name,
            company_principles=request.company_principles
        )
        job = db.get_job(job_id)
        return {
            "message": "Job created successfully", 
            "job_id": job_id, 
            "job": job,
            "company_name": company_name
        }
    except Exception as e:
        # Handle case where company_name column might not exist
        error_msg = str(e)
        logger.error(f"Error creating job: {error_msg}", exc_info=True)
        if "company_name" in error_msg.lower() or "invalid identifier" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="Database error: company_name column may not exist in JOBS table. Please contact admin."
            )
        raise HTTPException(status_code=500, detail=f"Failed to create job: {error_msg}")


@router.put("/{job_id}")
def update_job(job_id: int, request: UpdateJobRequest, current_user: dict = Depends(get_current_user)):
    """Update a job (recruiter only). Recruiters can only update jobs from their company."""
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # Check if user is recruiter or admin
    if user_role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Only recruiters can update jobs")
    
    # Check if job exists
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # If recruiter (not admin), verify job belongs to their company
    if user_role == "recruiter":
        user_data = db.get_user_by_id(current_user.get("user_id"))
        if user_data:
            company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
            if company_name:
                job_company = job.get("COMPANY_NAME") or job.get("company_name")
                if job_company != company_name:
                    raise HTTPException(status_code=403, detail="Cannot update job from another company")
    
    success = db.update_job(
        job_id=job_id,
        title=request.title,
        description=request.description,
        department=request.department,
        company_principles=request.company_principles
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update job")
    
    return {"message": "Job updated successfully", "job": db.get_job(job_id)}


@router.delete("/{job_id}")
def delete_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a job (recruiter only). Recruiters can only delete jobs from their company."""
    # Normalize role to lowercase for comparison
    user_role = current_user.get("role", "").lower() if current_user.get("role") else ""
    
    # Check if user is recruiter or admin
    if user_role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Only recruiters can delete jobs")
    
    # Check if job exists
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # If recruiter (not admin), verify job belongs to their company
    if user_role == "recruiter":
        user_data = db.get_user_by_id(current_user.get("user_id"))
        if user_data:
            company_name = user_data.get("COMPANY_NAME") or user_data.get("company_name")
            if company_name:
                job_company = job.get("COMPANY_NAME") or job.get("company_name")
                if job_company != company_name:
                    raise HTTPException(status_code=403, detail="Cannot delete job from another company")
    
    success = db.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete job")
    
    return {"message": "Job deleted successfully"}
