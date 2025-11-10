from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.core.deps import get_gemini_service, get_elevenlabs_service, get_did_service, get_webgazer_service
from app.db import snowflake_client
from app.services import grading_service
from app.utils.auth_utils import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/interviews", tags=["Interviews"])

# simple in-memory session store for demo/testing
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Interview eligibility threshold (90%)
INTERVIEW_THRESHOLD = 90.0


class StartInterviewRequest(BaseModel):
    candidate_id: Optional[int] = None
    job_id: int


class NextInterviewRequest(BaseModel):
    session_id: str
    response_text: str


class EndInterviewRequest(BaseModel):
    session_id: str


class EyeMetricsRequest(BaseModel):
    session_id: str
    gaze_data: Dict[str, Any]


@router.get("/eligibility")
def check_interview_eligibility(current_user: dict = Depends(get_current_user)):
    """
    Check if the current user is eligible for interview (OA score >= 90%)
    Optimized for faster response
    """
    try:
        # Get candidate by email
        user_email = current_user.get('email')
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
        
        logger.info(f"🔍 Checking eligibility for user: {user_email}")
        
        # Find candidate by email - simplified query
        from app.db.snowflake_client import get_connection
        
        candidate_ids = []
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ID FROM CANDIDATES WHERE UPPER(EMAIL) = UPPER(%s) LIMIT 10",
                    (user_email,)
                )
                candidates = cursor.fetchall()
                if candidates:
                    candidate_ids = [c[0] for c in candidates]
                cursor.close()
        except Exception as e:
            logger.error(f"Error querying candidates: {str(e)}")
            return {
                "eligible": False,
                "reason": "Error checking candidate records",
                "best_score": None,
                "threshold": INTERVIEW_THRESHOLD
            }
        
        logger.info(f"Found {len(candidate_ids)} candidate record(s) for email: {user_email}")
        
        if not candidate_ids:
            return {
                "eligible": False,
                "reason": "No candidate record found. Please apply for a job first.",
                "best_score": None,
                "threshold": INTERVIEW_THRESHOLD
            }
        
        # Check eligibility for the first candidate (most recent)
        # If they have multiple applications, we'll check the first one for speed
        try:
            candidate_id = candidate_ids[0]
            logger.info(f"Checking eligibility for candidate_id: {candidate_id}")
            eligibility = grading_service.check_interview_eligibility(candidate_id, INTERVIEW_THRESHOLD)
            
            # Return simplified response without debug info to speed things up
            return {
                "eligible": eligibility.get("eligible", False),
                "reason": eligibility.get("reason", "Unknown"),
                "best_score": eligibility.get("best_score"),
                "threshold": eligibility.get("threshold", INTERVIEW_THRESHOLD)
            }
        except Exception as e:
            logger.error(f"Error checking eligibility for candidate {candidate_ids[0]}: {str(e)}")
            return {
                "eligible": False,
                "reason": f"Error checking eligibility: {str(e)}",
                "best_score": None,
                "threshold": INTERVIEW_THRESHOLD
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking eligibility: {str(e)}", exc_info=True)
        return {
            "eligible": False,
            "reason": f"Error checking eligibility: {str(e)}",
            "best_score": None,
            "threshold": INTERVIEW_THRESHOLD
        }


@router.post("/start")
def start_interview(
    request: StartInterviewRequest,
    gemini=Depends(get_gemini_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Start an interview session. Requires OA score > 90%
    """
    # Get candidate by email if candidate_id not provided
    candidate = None
    if request.candidate_id:
        candidate = snowflake_client.get_candidate(request.candidate_id)
    else:
        # Find candidate by email
        user_email = current_user.get('email')
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not found")
        candidate = snowflake_client.get_candidate_by_email(user_email)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate_id = candidate.get('ID') or candidate.get('id')
    if not candidate_id:
        raise HTTPException(status_code=400, detail="Candidate ID not found")
    
    # Check interview eligibility
    eligibility = grading_service.check_interview_eligibility(candidate_id, INTERVIEW_THRESHOLD)
    if not eligibility["eligible"]:
        raise HTTPException(
            status_code=403,
            detail=f"Not eligible for interview: {eligibility['reason']}"
        )
    
    # Verify user owns this candidate record
    user_email = current_user.get('email', '').lower()
    candidate_email = candidate.get('EMAIL', '').lower()
    if user_email != candidate_email:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to start an interview for this candidate"
        )
    
    # Get job details
    job = snowflake_client.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate interview questions
    questions = gemini.generate_questions(job.get("description", ""), n=5)
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "candidate_id": candidate_id, 
        "job_id": request.job_id, 
        "questions": questions, 
        "pos": 0,
        "responses": []
    }
    
    # Return first question
    first = questions[0] if questions else None
    return {"session_id": session_id, "first_question": first}


@router.post("/next")
def next_interview(
    request: NextInterviewRequest,
    gemini=Depends(get_gemini_service),
    tts=Depends(get_elevenlabs_service),
    did=Depends(get_did_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit response to current question and get next question
    """
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user owns this session
    candidate = snowflake_client.get_candidate(session["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    user_email = current_user.get('email', '').lower()
    candidate_email = candidate.get('EMAIL', '').lower()
    if user_email != candidate_email:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this interview session"
        )
    
    # Evaluate response
    evaln = gemini.evaluate_response(request.response_text)
    
    # Store response
    current_question = session["questions"][session["pos"]] if session["pos"] < len(session["questions"]) else None
    session["responses"].append({
        "question": current_question,
        "response": request.response_text,
        "evaluation": evaln
    })
    
    # Advance position and pick next question
    session["pos"] += 1
    next_q = None
    if session["pos"] < len(session["questions"]):
        next_q = session["questions"][session["pos"]]
    
    # Synthesize audio and avatar video for the next question if present
    audio = None
    video = None
    if next_q:
        audio = tts.synthesize_voice(next_q["text"])
        video = did.generate_avatar_video(audio.get("audio_url"))

    return {"evaluation": evaln, "next_question": next_q, "audio": audio, "video": video}


@router.post("/end")
def end_interview(
    request: EndInterviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    End interview session and save results
    """
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user owns this session
    candidate = snowflake_client.get_candidate(session["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    user_email = current_user.get('email', '').lower()
    candidate_email = candidate.get('EMAIL', '').lower()
    if user_email != candidate_email:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this interview session"
        )
    
    # Calculate scores (simplified - you can enhance this)
    responses = session.get("responses", [])
    total_questions = len(session.get("questions", []))
    answered_questions = len(responses)
    
    # Calculate average engagement and AI scores from evaluations
    engagement_scores = []
    ai_scores = []
    transcript_parts = []
    
    for resp in responses:
        eval_data = resp.get("evaluation", {})
        if isinstance(eval_data, dict):
            engagement_scores.append(eval_data.get("engagement_score", 0.5))
            ai_scores.append(eval_data.get("ai_score", 0.5))
        transcript_parts.append(f"Q: {resp.get('question', {}).get('text', '')}\nA: {resp.get('response', '')}")
    
    avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.5
    avg_ai_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0.5
    transcript = "\n\n".join(transcript_parts)
    
    # Save interview to database
    try:
        interview_id = snowflake_client.create_interview(
            candidate_id=session["candidate_id"],
            transcript=transcript,
            engagement_score=avg_engagement,
            ai_score=avg_ai_score,
            notes=f"Interview completed. {answered_questions}/{total_questions} questions answered."
        )
        
        # Remove session from memory
        SESSIONS.pop(request.session_id, None)
        
        summary = {
            "message": "Interview completed successfully",
            "interview_id": interview_id,
            "questions_asked": total_questions,
            "questions_answered": answered_questions,
            "engagement_score": avg_engagement,
            "ai_score": avg_ai_score
        }
        
        return {"summary": summary}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving interview: {str(e)}")


@router.post("/metrics/eye")
def metrics_eye(
    request: EyeMetricsRequest,
    webgazer=Depends(get_webgazer_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit eye tracking metrics for interview session
    """
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify user owns this session
    candidate = snowflake_client.get_candidate(session["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    user_email = current_user.get('email', '').lower()
    candidate_email = candidate.get('EMAIL', '').lower()
    if user_email != candidate_email:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this interview session"
        )
    
    metrics = webgazer.analyze_gaze(request.gaze_data)
    return {"metrics": metrics}
