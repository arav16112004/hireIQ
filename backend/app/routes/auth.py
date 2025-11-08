from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta
from app.utils.auth_utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.db import snowflake_client

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    role: str = Field(default="candidate", pattern="^(candidate|recruiter|admin)$")
    company_name: Optional[str] = None  # Required for recruiters


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    company_name: Optional[str] = None
    is_active: bool
    email_verified: bool


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@router.post("/register")
def register(request: RegisterRequest):
    """
    Register a new user account
    
    Roles:
    - candidate: Job seekers
    - recruiter: Hiring managers/employers
    - admin: Platform administrators
    """
    # Check if user exists
    existing = snowflake_client.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role-specific requirements
    if request.role == "recruiter" and not request.company_name:
        raise HTTPException(
            status_code=400,
            detail="Company name is required for recruiter accounts"
        )
    
    # Hash password and create user
    hashed_pw = hash_password(request.password)
    user_id = snowflake_client.create_user(
        email=request.email,
        password_hash=hashed_pw,
        name=request.name,
        role=request.role,
        company_name=request.company_name
    )
    
    return {
        "message": f"{request.role.capitalize()} account created successfully",
        "user_id": user_id,
        "role": request.role
    }


@router.post("/login")
def login(request: LoginRequest):
    """
    Login with email and password
    
    Returns JWT access token
    """
    # Get user from database
    user = snowflake_client.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password
    if not verify_password(request.password, user["PASSWORD"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is active
    if not user.get("IS_ACTIVE", True):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Update last login timestamp
    snowflake_client.update_user_last_login(user["ID"])
    
    # Create JWT token with role information
    token = create_access_token(
        data={
            "sub": user["ID"],
            "email": user["EMAIL"],
            "role": user["ROLE"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["ID"],
            "email": user["EMAIL"],
            "name": user["NAME"],
            "role": user["ROLE"],
            "company_name": user.get("COMPANY_NAME")
        }
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information
    
    Requires: Valid JWT token
    """
    # Fetch full user details from database
    user = snowflake_client.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["ID"],
        "email": user["EMAIL"],
        "name": user["NAME"],
        "role": user["ROLE"],
        "company_name": user.get("COMPANY_NAME"),
        "is_active": user.get("IS_ACTIVE", True),
        "email_verified": user.get("EMAIL_VERIFIED", False)
    }


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user
    
    Note: Since we're using JWT, the token remains valid until expiration.
    Client should delete the token from storage.
    """
    return {"message": "Logged out successfully"}


# ============================================================
# ROLE-SPECIFIC REGISTRATION ENDPOINTS
# ============================================================

class CandidateRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)


class RecruiterRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    company_name: str = Field(..., min_length=2)


@router.post("/register/candidate")
def register_candidate(request: CandidateRegisterRequest):
    """
    Register as a job seeker/candidate
    
    Simplified endpoint - role is automatically set to 'candidate'
    Also creates an empty profile for storing resume later
    """
    # Check if user exists
    existing = snowflake_client.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create candidate user
    hashed_pw = hash_password(request.password)
    user_id = snowflake_client.create_user(
        email=request.email,
        password_hash=hashed_pw,
        name=request.name,
        role="candidate"
    )
    
    # Create empty candidate profile (they'll complete it later)
    profile_id = snowflake_client.create_candidate_profile(user_id)
    
    return {
        "message": "Candidate account created successfully",
        "user_id": user_id,
        "profile_id": profile_id,
        "role": "candidate",
        "next_step": "Complete your profile at /candidate/profile"
    }


@router.post("/register/recruiter")
def register_recruiter(request: RecruiterRegisterRequest):
    """
    Register as an employer/recruiter
    
    Simplified endpoint - role is automatically set to 'recruiter'
    Requires company_name
    """
    # Check if user exists
    existing = snowflake_client.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create recruiter
    hashed_pw = hash_password(request.password)
    user_id = snowflake_client.create_user(
        email=request.email,
        password_hash=hashed_pw,
        name=request.name,
        role="recruiter",
        company_name=request.company_name
    )
    
    return {
        "message": "Recruiter account created successfully",
        "user_id": user_id,
        "role": "recruiter",
        "company_name": request.company_name
    }