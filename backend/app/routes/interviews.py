from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import uuid

from app.core.deps import get_gemini_service, get_elevenlabs_service, get_did_service, get_webgazer_service
from app.db import snowflake_client

router = APIRouter(prefix="/interviews", tags=["Interviews"])

# simple in-memory session store for demo/testing
SESSIONS: Dict[str, Dict[str, Any]] = {}


@router.post("/start")
def start_interview(candidate_id: int, job_id: int, gemini=Depends(get_gemini_service)):
    job = snowflake_client.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    questions = gemini.generate_questions(job.get("description", ""), n=5)
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"candidate_id": candidate_id, "job_id": job_id, "questions": questions, "pos": 0}
    # return first question
    first = questions[0] if questions else None
    # Note: insert_metrics is not yet implemented in snowflake_client
    # snowflake_client.insert_metrics({"event": "interview_started", "candidate_id": candidate_id, "job_id": job_id})
    return {"session_id": session_id, "first_question": first}


@router.post("/next")
def next_interview(
    session_id: str,
    response_text: str,
    gemini=Depends(get_gemini_service),
    tts=Depends(get_elevenlabs_service),
    did=Depends(get_did_service),
):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    evaln = gemini.evaluate_response(response_text)
    # advance position and pick next question
    session["pos"] += 1
    next_q = None
    if session["pos"] < len(session["questions"]):
        next_q = session["questions"][session["pos"]]
    # synthesize audio and avatar video for the next question if present
    audio = None
    video = None
    if next_q:
        audio = tts.synthesize_voice(next_q["text"])
        video = did.generate_avatar_video(audio.get("audio_url"))

    # Note: insert_metrics is not yet implemented in snowflake_client
    # snowflake_client.insert_metrics({"event": "question_answered", "session_id": session_id, "evaluation": evaln})
    return {"evaluation": evaln, "next_question": next_q, "audio": audio, "video": video}


@router.post("/end")
def end_interview(session_id: str, gemini=Depends(get_gemini_service)):
    session = SESSIONS.pop(session_id, None)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    # produce a tiny summary
    summary = {"message": "Interview ended", "questions_asked": len(session.get("questions", []))}
    # Note: insert_metrics is not yet implemented in snowflake_client
    # snowflake_client.insert_metrics({"event": "interview_ended", "session_id": session_id, "summary": summary})
    return {"summary": summary}


@router.post("/metrics/eye")
def metrics_eye(session_id: str, gaze_data: dict, webgazer=Depends(get_webgazer_service)):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")
    metrics = webgazer.analyze_gaze(gaze_data)
    # Note: insert_metrics is not yet implemented in snowflake_client
    # snowflake_client.insert_metrics({"event": "eye_metrics", "session_id": session_id, "metrics": metrics})
    return {"metrics": metrics}
