from backend.app.db import snowflake_client as db
from backend.app.services.gemini_service import GeminiService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional


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


router = APIRouter(prefix="/v1/jobs")


@router.get("/")
def list_jobs():
    """List all available jobs."""
    return {"jobs": db.get_all_jobs()}


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