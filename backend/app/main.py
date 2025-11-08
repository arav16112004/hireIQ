from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import candidates, interviews, jobs, system, oa, oa_admin, auth, candidate_profile
from app.core.config import settings

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

