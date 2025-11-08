from fastapi import APIRouter

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def system_status():
    return {"status": "operational"}

