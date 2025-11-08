from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import candidates, interviews, jobs, system, oa, oa_admin
from app.core.config import settings

app = FastAPI(
    title="TeamSero API",
    description="AI-Driven Hiring Platform with OA Assessment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(candidates.router)
app.include_router(interviews.router)
app.include_router(jobs.router)
app.include_router(system.router)
app.include_router(oa.router)
app.include_router(oa_admin.router)


@app.get("/")
def root():
    return {
        "message": "TeamSero API",
        "version": "1.0.0",
        "docs": "/docs",
        "database": settings.snowflake_database
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

