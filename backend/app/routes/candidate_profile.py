"""
Candidate Profile Routes
Manage persistent candidate profiles (resume, skills, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.db import snowflake_client
from app.utils.auth_utils import get_current_candidate, get_current_user
from app.core.logger import logger


router = APIRouter(prefix="/candidate/profile", tags=["Candidate Profile"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ProfileUpdateRequest(BaseModel):
    resume_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[str] = None  # Comma-separated: "Python, JavaScript, React"
    experience_years: Optional[int] = None
    education: Optional[str] = None
    bio: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    resume_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[str] = None
    experience_years: Optional[int] = None
    education: Optional[str] = None
    bio: Optional[str] = None
    is_profile_complete: bool
    created_at: str
    updated_at: str


# ============================================================
# PROFILE ENDPOINTS
# ============================================================

@router.get("/", response_model=ProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_candidate)):
    """
    Get current candidate's profile
    
    Requires: Candidate role
    """
    profile = snowflake_client.get_candidate_profile_by_user_id(current_user["user_id"])
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "id": profile["ID"],
        "user_id": profile["USER_ID"],
        "resume_url": profile.get("RESUME_URL"),
        "phone": profile.get("PHONE"),
        "location": profile.get("LOCATION"),
        "linkedin_url": profile.get("LINKEDIN_URL"),
        "portfolio_url": profile.get("PORTFOLIO_URL"),
        "skills": profile.get("SKILLS"),
        "experience_years": profile.get("EXPERIENCE_YEARS"),
        "education": profile.get("EDUCATION"),
        "bio": profile.get("BIO"),
        "is_profile_complete": profile.get("IS_PROFILE_COMPLETE", False),
        "created_at": str(profile.get("CREATED_AT")),
        "updated_at": str(profile.get("UPDATED_AT"))
    }


@router.put("/")
def update_my_profile(
    updates: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_candidate)
):
    """
    Update candidate profile
    
    You can update any fields (resume, phone, skills, etc.)
    Profile is marked complete when resume, phone, and location are provided.
    
    Requires: Candidate role
    """
    # Check if profile exists, create if not
    profile = snowflake_client.get_candidate_profile_by_user_id(current_user["user_id"])
    if not profile:
        snowflake_client.create_candidate_profile(current_user["user_id"])
    
    # Update profile
    success = snowflake_client.update_candidate_profile(
        user_id=current_user["user_id"],
        resume_url=updates.resume_url,
        phone=updates.phone,
        location=updates.location,
        linkedin_url=updates.linkedin_url,
        portfolio_url=updates.portfolio_url,
        skills=updates.skills,
        experience_years=updates.experience_years,
        education=updates.education,
        bio=updates.bio
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    logger.info(f"Candidate profile updated for user {current_user['user_id']}")
    
    return {
        "message": "Profile updated successfully",
        "user_id": current_user["user_id"]
    }


@router.post("/complete")
def complete_profile_setup(current_user: dict = Depends(get_current_candidate)):
    """
    Mark profile as complete (after uploading resume, etc.)
    
    Useful for onboarding flow
    """
    profile = snowflake_client.get_candidate_profile_by_user_id(current_user["user_id"])
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Please update your profile first.")
    
    # Check if required fields are present
    if not profile.get("RESUME_URL"):
        raise HTTPException(status_code=400, detail="Resume is required to complete profile")
    
    if not profile.get("PHONE"):
        raise HTTPException(status_code=400, detail="Phone number is required to complete profile")
    
    if not profile.get("LOCATION"):
        raise HTTPException(status_code=400, detail="Location is required to complete profile")
    
    return {
        "message": "Profile is complete!",
        "profile_complete": True
    }


@router.get("/check-completion")
def check_profile_completion(current_user: dict = Depends(get_current_candidate)):
    """
    Check if profile is complete
    
    Useful for showing "Complete your profile" prompts in UI
    """
    profile = snowflake_client.get_candidate_profile_by_user_id(current_user["user_id"])
    
    if not profile:
        return {
            "profile_exists": False,
            "is_complete": False,
            "missing_fields": ["resume", "phone", "location"]
        }
    
    missing_fields = []
    if not profile.get("RESUME_URL"):
        missing_fields.append("resume")
    if not profile.get("PHONE"):
        missing_fields.append("phone")
    if not profile.get("LOCATION"):
        missing_fields.append("location")
    
    return {
        "profile_exists": True,
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "profile": {
            "has_resume": bool(profile.get("RESUME_URL")),
            "has_phone": bool(profile.get("PHONE")),
            "has_location": bool(profile.get("LOCATION")),
            "has_skills": bool(profile.get("SKILLS")),
            "has_linkedin": bool(profile.get("LINKEDIN_URL"))
        }
    }

