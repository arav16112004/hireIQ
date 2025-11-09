# backend/app/routes/integrity.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.db import snowflake_client

router = APIRouter(prefix="/api/integrity", tags=["Integrity"])

# ============ MODELS ============
class IntegrityEvent(BaseModel):
    t: int
    score: int
    glanceStats: dict
    head: float

# ============ ROUTES ============
@router.post("/")
async def record_integrity(event: IntegrityEvent):
    """
    Receives live integrity scores (eye + head tracking) from frontend.
    Stores to Snowflake for later recruiter review.
    """
    try:
        conn = snowflake_client.get_connection()
        cursor = conn.cursor()

        timestamp = datetime.utcfromtimestamp(event.t / 1000.0)
        score = event.score
        glance_count = event.glanceStats.get("recent", 0)
        max_bucket = event.glanceStats.get("maxBucket", 0)
        head = event.head

        cursor.execute(
            """
            INSERT INTO candidate_integrity (timestamp, score, glance_count, max_bucket, head)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (timestamp, score, glance_count, max_bucket, head),
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Optional: flag if suspicious
        flagged = score > 75
        return {"status": "ok", "flagged": flagged}

    except Exception as e:
        print("Integrity insert error:", e)
        raise HTTPException(status_code=500, detail=str(e))
