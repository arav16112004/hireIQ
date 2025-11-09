from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta
import os, jwt

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
    company_name: Optional[str] = None


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
    """Register a new user account"""
    existing = snowflake_client.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if request.role == "recruiter" and not request.company_name:
        raise HTTPException(status_code=400, detail="Company name required for recruiter")

    hashed_pw = hash_password(request.password)
    user_id = snowflake_client.create_user(
        email=request.email,
        password_hash=hashed_pw,
        name=request.name,
        role=request.role,
        company_name=request.company_name
    )

    # Normalize role to lowercase for consistency
    user_role = request.role.lower() if isinstance(request.role, str) else request.role
    
    token = create_access_token(
        data={"sub": str(user_id), "email": request.email, "role": user_role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": request.email,
            "name": request.name,
            "role": user_role,
            "company_name": request.company_name
        }
    }


@router.post("/login")
def login(request: LoginRequest):
    """Login with email and password"""
    user = snowflake_client.get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["PASSWORD"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("IS_ACTIVE", True):
        raise HTTPException(status_code=403, detail="Account is deactivated")

    snowflake_client.update_user_last_login(user["ID"])

    # Normalize role to lowercase for consistency
    user_role = user.get("ROLE") or user.get("role", "candidate")
    if isinstance(user_role, str):
        user_role = user_role.lower()
    
    token = create_access_token(
        data={"sub": str(user["ID"]), "email": user["EMAIL"], "role": user_role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["ID"],
            "email": user["EMAIL"],
            "name": user["NAME"],
            "role": user_role,
            "company_name": user.get("COMPANY_NAME") or user.get("company_name")
        }
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Return info about current authenticated user"""
    user = snowflake_client.get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Normalize role to lowercase for consistency
    user_role = user.get("ROLE") or user.get("role", "candidate")
    if isinstance(user_role, str):
        user_role = user_role.lower()

    return {
        "id": user["ID"],
        "email": user["EMAIL"],
        "name": user["NAME"],
        "role": user_role,
        "company_name": user.get("COMPANY_NAME") or user.get("company_name"),
        "is_active": user.get("IS_ACTIVE", True),
        "email_verified": user.get("EMAIL_VERIFIED", False)
    }


@router.post("/logout")
def logout(_: dict = Depends(get_current_user)):
    """Logout (client must delete stored token)"""
    return {"message": "Logged out successfully"}


# ============================================================
# ROLE-SPECIFIC ENDPOINTS
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
    existing = snowflake_client.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(request.password)
    user_id = snowflake_client.create_user(
        email=request.email,
        password_hash=hashed_pw,
        name=request.name,
        role="candidate"
    )

    profile_id = snowflake_client.create_candidate_profile(user_id)
    return {
        "message": "Candidate account created",
        "user_id": user_id,
        "profile_id": profile_id,
        "role": "candidate"
    }


@router.post("/register/recruiter")
def register_recruiter(request: RecruiterRegisterRequest):
    existing = snowflake_client.get_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(request.password)
    user_id = snowflake_client.create_user(
        email=request.email,
        password_hash=hashed_pw,
        name=request.name,
        role="recruiter",
        company_name=request.company_name
    )

    return {
        "message": "Recruiter account created",
        "user_id": user_id,
        "role": "recruiter",
        "company_name": request.company_name
    }
