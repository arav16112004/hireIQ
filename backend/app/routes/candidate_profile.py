"""
Candidate Profile Routes
Manage persistent candidate profiles (resume, skills, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import os
from pathlib import Path

from app.db import snowflake_client
from app.utils.auth_utils import get_current_candidate, get_current_user
from app.core.logger import logger
from app.services.gemini_service import GeminiService

# Try to import PyMuPDF for PDF processing
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


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
    description: Optional[str] = None  # Resume summary from Gemini


class ProfileResponse(BaseModel):
    id: int
    user_id: int  # This is the candidate_id (from CANDIDATES table)
    email: Optional[str] = None  # Email from user account
    resume_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[str] = None  # Comma-separated string (converted from array)
    experience_years: Optional[int] = None
    education: Optional[str] = None
    bio: Optional[str] = None
    description: Optional[str] = None  # Resume summary from Gemini
    is_profile_complete: bool
    created_at: str


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
    
    # Handle both uppercase and lowercase column names from Snowflake
    def get_field(field_name: str, default=None):
        return profile.get(field_name.upper()) or profile.get(field_name.lower()) or default
    
    # Handle skills array - convert to comma-separated string
    skills_data = get_field("SKILLS")
    if isinstance(skills_data, list):
        skills_str = ", ".join([str(s) for s in skills_data if s])
    else:
        skills_str = skills_data
    
    # Get user_id from candidate_profiles (which is the candidate_id)
    user_id = get_field("USER_ID") or get_field("ID", 0)
    
    # Get email from user account
    from app.db.snowflake_client import get_user_by_id
    user = get_user_by_id(current_user["user_id"])
    email = None
    if user:
        email = user.get("EMAIL") or user.get("email")
    
    return {
        "id": get_field("ID", 0),
        "user_id": user_id,
        "email": email,
        "resume_url": get_field("RESUME_URL"),
        "phone": get_field("PHONE"),
        "location": get_field("LOCATION"),
        "linkedin_url": get_field("LINKEDIN_URL"),
        "portfolio_url": get_field("PORTFOLIO_URL"),
        "skills": skills_str,
        "experience_years": get_field("EXPERIENCE_YEARS"),
        "education": get_field("EDUCATION"),
        "bio": get_field("BIO"),
        "description": get_field("DESCRIPTION"),
        "is_profile_complete": bool(get_field("IS_PROFILE_COMPLETE", False)),
        "created_at": str(get_field("CREATED_AT", ""))
    }


@router.put("/", response_model=ProfileResponse)
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
    
    # Log what we received with types - this is critical for debugging
    logger.info(f"=== PROFILE UPDATE REQUEST ===")
    logger.info(f"User ID: {current_user['user_id']}")
    logger.info(f"  phone: {repr(updates.phone)} (type: {type(updates.phone).__name__}, is None: {updates.phone is None})")
    logger.info(f"  location: {repr(updates.location)} (type: {type(updates.location).__name__}, is None: {updates.location is None})")
    logger.info(f"  linkedin_url: {repr(updates.linkedin_url)} (type: {type(updates.linkedin_url).__name__}, is None: {updates.linkedin_url is None})")
    logger.info(f"  portfolio_url: {repr(updates.portfolio_url)} (type: {type(updates.portfolio_url).__name__}, is None: {updates.portfolio_url is None})")
    logger.info(f"  skills: {repr(updates.skills)} (type: {type(updates.skills).__name__})")
    logger.info(f"  experience_years: {updates.experience_years} (type: {type(updates.experience_years).__name__})")
    logger.info(f"  education: {repr(updates.education)} (type: {type(updates.education).__name__})")
    logger.info(f"  bio: {repr(updates.bio)} (type: {type(updates.bio).__name__})")
    logger.info(f"  resume_url: {repr(updates.resume_url)} (type: {type(updates.resume_url).__name__})")
    logger.info(f"  description: {repr(updates.description)} (type: {type(updates.description).__name__})")
    
    # Convert None to empty string for string fields to ensure they're sent (Pydantic might convert empty strings to None)
    # This ensures that if a field is provided (even as empty string), it gets processed
    phone_val = updates.phone if updates.phone is not None else None
    linkedin_val = updates.linkedin_url if updates.linkedin_url is not None else None
    portfolio_val = updates.portfolio_url if updates.portfolio_url is not None else None
    
    logger.info(f"After processing - phone: {repr(phone_val)}, linkedin: {repr(linkedin_val)}, portfolio: {repr(portfolio_val)}")
    
    # Update profile - pass values as-is (backend will handle empty strings)
    success = snowflake_client.update_candidate_profile(
        user_id=current_user["user_id"],
        resume_url=updates.resume_url,
        phone=phone_val,
        location=updates.location,
        linkedin_url=linkedin_val,
        portfolio_url=portfolio_val,
        skills=updates.skills,
        experience_years=updates.experience_years,
        education=updates.education,
        bio=updates.bio,
        description=updates.description
    )
    
    if not success:
        logger.error(f"Failed to update profile for user {current_user['user_id']} - update_candidate_profile returned False")
        raise HTTPException(status_code=400, detail="No updates provided or update failed")
    
    logger.info(f"Candidate profile updated for user {current_user['user_id']}")
    
    # Fetch and return the updated profile
    updated_profile = snowflake_client.get_candidate_profile_by_user_id(current_user["user_id"])
    
    if not updated_profile:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated profile")
    
    # Handle both uppercase and lowercase column names from Snowflake
    def get_field(field_name: str, default=None):
        return updated_profile.get(field_name.upper()) or updated_profile.get(field_name.lower()) or default
    
    # Handle skills array - convert to comma-separated string
    skills_data = get_field("SKILLS")
    if isinstance(skills_data, list):
        skills_str = ", ".join([str(s) for s in skills_data if s])
    else:
        skills_str = skills_data
    
    # Get user_id from candidate_profiles (which is the candidate_id)
    user_id = get_field("USER_ID") or get_field("ID", 0)
    
    # Get email from user account
    from app.db.snowflake_client import get_user_by_id
    user = get_user_by_id(current_user["user_id"])
    email = None
    if user:
        email = user.get("EMAIL") or user.get("email")
    
    return {
        "id": get_field("ID", 0),
        "user_id": user_id,
        "email": email,
        "resume_url": get_field("RESUME_URL"),
        "phone": get_field("PHONE"),
        "location": get_field("LOCATION"),
        "linkedin_url": get_field("LINKEDIN_URL"),
        "portfolio_url": get_field("PORTFOLIO_URL"),
        "skills": skills_str,
        "experience_years": get_field("EXPERIENCE_YEARS"),
        "education": get_field("EDUCATION"),
        "bio": get_field("BIO"),
        "description": get_field("DESCRIPTION"),
        "is_profile_complete": bool(get_field("IS_PROFILE_COMPLETE", False)),
        "created_at": str(get_field("CREATED_AT", ""))
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
    
    # Check if required fields are present (handle both uppercase and lowercase)
    def get_field(field_name: str):
        return profile.get(field_name.upper()) or profile.get(field_name.lower())
    
    if not get_field("RESUME_URL"):
        raise HTTPException(status_code=400, detail="Resume is required to complete profile")
    
    if not get_field("PHONE"):
        raise HTTPException(status_code=400, detail="Phone number is required to complete profile")
    
    if not get_field("LOCATION"):
        raise HTTPException(status_code=400, detail="Location is required to complete profile")
    
    return {
        "message": "Profile is complete!",
        "profile_complete": True
    }


@router.post("/resume", response_model=ProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_candidate)
):
    """
    Upload resume file for candidate profile and generate summary using Gemini
    
    Requires: Candidate role
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Check if PyMuPDF is available
    if fitz is None:
        raise HTTPException(
            status_code=500, 
            detail="PDF processing not available. PyMuPDF is required for resume analysis."
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = upload_dir / f"{current_user['user_id']}_{file.filename}"
    resume_url = None
    description = None
    
    try:
        # Read file content
        content = await file.read()
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        resume_url = f"uploads/{current_user['user_id']}_{file.filename}"
        logger.info(f"Resume URL set to: {resume_url}")
        
        # Ensure candidate profile exists before updating
        try:
            snowflake_client.create_candidate_profile(current_user["user_id"])
            logger.info(f"Ensured candidate profile exists for user {current_user['user_id']}")
        except Exception as e:
            logger.warning(f"Error ensuring candidate profile exists: {str(e)}")
        
        # Extract text from PDF
        resume_text = ""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                resume_text += page.get_text("text")
            doc.close()
            logger.info(f"Extracted {len(resume_text)} characters from PDF")
        except Exception as e:
            logger.warning(f"Failed to extract text from PDF: {str(e)}")
            resume_text = ""
        
        # Generate summary using Gemini if we have resume text
        description = None
        if resume_text.strip():
            try:
                logger.info("Calling Gemini to generate resume summary...")
                gemini = GeminiService()
                result = gemini.extract_skills(resume_text, job_desc=None)
                description = result.get("summary", "").strip() if result.get("summary") else None
                if description:
                    logger.info(f"✅ Generated resume summary ({len(description)} chars): {description[:100]}...")
                else:
                    logger.warning("⚠️ Gemini returned empty summary")
            except Exception as e:
                logger.error(f"❌ Failed to generate resume summary with Gemini: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                description = None
        else:
            logger.warning("⚠️ Resume text is empty, skipping Gemini analysis")
        
        # Update candidate profile with resume URL and description
        logger.info(f"Preparing to update profile with resume_url: {resume_url}")
        logger.info(f"Description to update: {description[:100] if description else 'None'}...")
        
        # Always update resume_url, optionally update description
        update_kwargs = {
            "user_id": current_user["user_id"],
            "resume_url": resume_url
        }
        
        if description and description.strip():
            update_kwargs["description"] = description.strip()
            logger.info(f"✅ Will update description: {description[:100]}...")
        else:
            logger.info("⚠️ No description to update (empty or None)")
        
        logger.info(f"Calling update_candidate_profile with: user_id={update_kwargs['user_id']}, resume_url={update_kwargs['resume_url']}, description={'present' if 'description' in update_kwargs else 'not present'}")
        
        success = snowflake_client.update_candidate_profile(**update_kwargs)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile with resume URL")
        
        logger.info(f"Resume uploaded for user {current_user['user_id']}: {resume_url}")
        if description:
            logger.info(f"Resume summary generated: {description[:100]}...")
        
        # Fetch and return the updated profile
        updated_profile = snowflake_client.get_candidate_profile_by_user_id(current_user["user_id"])
        
        if not updated_profile:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated profile")
        
        # Handle both uppercase and lowercase column names from Snowflake
        def get_field(field_name: str, default=None):
            return updated_profile.get(field_name.upper()) or updated_profile.get(field_name.lower()) or default
        
        # Handle skills array - convert to comma-separated string
        skills_data = get_field("SKILLS")
        if isinstance(skills_data, list):
            skills_str = ", ".join([str(s) for s in skills_data if s])
        else:
            skills_str = skills_data
        
        # Get user_id from candidate_profiles (which is the candidate_id)
        user_id = get_field("USER_ID") or get_field("ID", 0)
        
        # Get email from user account
        from app.db.snowflake_client import get_user_by_id
        user = get_user_by_id(current_user["user_id"])
        email = None
        if user:
            email = user.get("EMAIL") or user.get("email")
        
        return {
            "id": get_field("ID", 0),
            "user_id": user_id,
            "email": email,
            "resume_url": get_field("RESUME_URL"),
            "phone": get_field("PHONE"),
            "location": get_field("LOCATION"),
            "linkedin_url": get_field("LINKEDIN_URL"),
            "portfolio_url": get_field("PORTFOLIO_URL"),
            "skills": skills_str,
            "experience_years": get_field("EXPERIENCE_YEARS"),
            "education": get_field("EDUCATION"),
            "bio": get_field("BIO"),
            "description": get_field("DESCRIPTION"),
            "is_profile_complete": bool(get_field("IS_PROFILE_COMPLETE", False)),
            "created_at": str(get_field("CREATED_AT", ""))
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        # Clean up file if database update failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")


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
    
    # Helper to get field (handle both uppercase and lowercase)
    def get_field(field_name: str):
        return profile.get(field_name.upper()) or profile.get(field_name.lower())
    
    missing_fields = []
    if not get_field("RESUME_URL"):
        missing_fields.append("resume")
    if not get_field("PHONE"):
        missing_fields.append("phone")
    if not get_field("LOCATION"):
        missing_fields.append("location")
    
    return {
        "profile_exists": True,
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "profile": {
            "has_resume": bool(get_field("RESUME_URL")),
            "has_phone": bool(get_field("PHONE")),
            "has_location": bool(get_field("LOCATION")),
            "has_skills": bool(get_field("SKILLS")),
            "has_linkedin": bool(get_field("LINKEDIN_URL"))
        }
    }

