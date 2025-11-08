"""FastAPI app entrypoint for TeamSero backend (AI interviewer).

This file wires routes together. Run via: uvicorn backend.app.main:app --reload
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import candidates, interviews, jobs, system, oa, oa_admin, auth, candidate_profile
from app.core.config import settings

# Get the backend directory (parent of app directory)
BACKEND_DIR = Path(__file__).parent.parent
STATIC_DIR = BACKEND_DIR / "static"

app = FastAPI(
    title="SeroHire API",
    description="AI-Driven Hiring Platform with OA Assessment",
    version="1.0.0"
)

# CORS middleware - Allow serohire.tech domains
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://serohire.tech",
    "https://www.serohire.tech",
    "https://app.serohire.tech",
    "https://api.serohire.tech",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for serving generated audio/video assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
app.include_router(auth.router)
app.include_router(candidate_profile.router)
app.include_router(candidates.router)
app.include_router(interviews.router)
app.include_router(jobs.router)
app.include_router(system.router)
app.include_router(oa.router)
app.include_router(oa_admin.router)


@app.get("/")
def root():
    return {
        "message": "SeroHire API - AI-Driven Hiring Platform",
        "version": "1.0.0",
        "domain": "serohire.tech",
        "docs": "/docs",
        "database": settings.snowflake_database
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
