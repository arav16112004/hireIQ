from fastapi import APIRouter

router = APIRouter(prefix="/interviews", tags=["Interviews"])

@router.get("/")
def list_interviews():
    return {"message": "Interviews endpoint - to be implemented"}

