from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

# Configuration from settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current authenticated user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "candidate")
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================

def require_role(allowed_roles: list):
    """
    Dependency factory to restrict access to specific roles
    
    Usage:
        @router.get("/admin/dashboard")
        def admin_dashboard(current_user = Depends(require_role(["admin"]))):
            ...
    
    Args:
        allowed_roles: List of roles allowed to access the endpoint
                      e.g., ["admin"], ["recruiter", "admin"]
    """
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "candidate")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# Convenience dependencies for common role checks
def get_current_recruiter(current_user: dict = Depends(require_role(["recruiter", "admin"]))):
    """Dependency to get current user (recruiter or admin only)"""
    return current_user


def get_current_admin(current_user: dict = Depends(require_role(["admin"]))):
    """Dependency to get current user (admin only)"""
    return current_user


def get_current_candidate(current_user: dict = Depends(require_role(["candidate"]))):
    """Dependency to get current user (candidate only)"""
    return current_user