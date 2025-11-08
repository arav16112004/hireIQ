from fastapi import APIRouter, UploadFile, Form, HTTPException, File
from pydantic import BaseModel
from typing import List, Optional
from backend.app.services.gemini_service import GeminiService
from backend.app.db import snowflake_client as db
import fitz  # PyMuPDF for PDF text extraction


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


router = APIRouter(prefix="/v1/candidates")

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
    job_description: str = Form("")
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # --- 1️⃣ Read resume text from PDF ---
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
        candidate_id = db.create_candidate(
            name=file.filename.replace('.pdf', ''),
            email="N/A",
            resume_url=f"uploads/{file.filename}",
            job_id=job_id
        )
        
        if fit_score < 85:
            db.update_candidate_stage(candidate_id, "rejected")
            return CandidateResponse(
                candidate_id=candidate_id,
                fit_score=fit_score,
                skills=skills,
                status="rejected",
                summary=summary
            )

        db.save_fit_score(candidate_id, fit_score, summary)
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


@router.get("/")
def list_jobs():
    """List all available jobs"""
    return {"jobs": db.get_all_jobs()}


@router.post("/match", response_model=JobMatchResponse)
def match_jobs(candidate_id: int):
    """Match jobs based on candidate ID"""
    # Get candidate and their extracted skills
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get all jobs to match against
    jobs = db.get_all_jobs()
    
    # Use Gemini to rank jobs
    gemini = GeminiService()
    matches = gemini.rank_jobs(candidate.get("skills", []), jobs)
    
    return JobMatchResponse(matches=matches)


@router.post("/match_by_skills", response_model=JobMatchResponse)
def match_jobs_by_skills(request: JobMatchRequest):
    """Match and rank jobs based on provided skills"""
    if not request.skills:
        raise HTTPException(status_code=400, detail="Skills list cannot be empty")
    
    jobs = db.get_all_jobs()
    gemini = GeminiService()
    matches = gemini.rank_jobs(request.skills, jobs)
    
    # Limit to top_k results if specified
    if request.top_k:
        matches = matches[:request.top_k]
    
    return JobMatchResponse(matches=matches)


  
