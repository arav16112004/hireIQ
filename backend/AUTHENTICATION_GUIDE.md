# 🔐 Authentication & Role-Based Access Control Guide

## Overview

Your API now supports **JWT-based authentication** with **role-based access control (RBAC)**.

### User Roles:
- **`candidate`** - Job seekers who take assessments
- **`recruiter`** - Hiring managers/employers who post jobs
- **`admin`** - Platform administrators

---

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
cd backend
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 2. Create Users Table in Snowflake

```bash
# Run the SQL script
snowsql -f users_table.sql
```

Or execute `backend/users_table.sql` in your Snowflake console.

### 3. Update .env with Secret Key

Add to `backend/.env`:

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📝 API Endpoints

### Register New User

```bash
# Register as CANDIDATE (default)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "password": "securepass123",
    "name": "John Candidate",
    "role": "candidate"
  }'

# Register as RECRUITER (requires company_name)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruiter@company.com",
    "password": "securepass123",
    "name": "Jane Recruiter",
    "role": "recruiter",
    "company_name": "TechCorp Inc"
  }'
```

**Response:**
```json
{
  "message": "Recruiter account created successfully",
  "user_id": 3,
  "role": "recruiter"
}
```

---

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruiter@company.com",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 3,
    "email": "recruiter@company.com",
    "name": "Jane Recruiter",
    "role": "recruiter",
    "company_name": "TechCorp Inc"
  }
}
```

---

### Get Current User Info

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "id": 3,
  "email": "recruiter@company.com",
  "name": "Jane Recruiter",
  "role": "recruiter",
  "company_name": "TechCorp Inc",
  "is_active": true,
  "email_verified": false
}
```

---

## 🛡️ Protecting Routes with RBAC

### Method 1: Require Any Authentication

```python
from fastapi import Depends
from app.utils.auth_utils import get_current_user

@router.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['email']}!"}
```

---

### Method 2: Require Specific Role

```python
from app.utils.auth_utils import get_current_recruiter, get_current_admin

# Only recruiters and admins
@router.post("/jobs")
def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_recruiter)
):
    return {"message": f"Job created by {current_user['email']}"}

# Only admins
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_admin)
):
    return {"message": "User deleted"}
```

---

### Method 3: Custom Role Requirements

```python
from app.utils.auth_utils import require_role

# Multiple roles allowed
@router.get("/dashboard")
def dashboard(current_user: dict = Depends(require_role(["recruiter", "admin"]))):
    return {"data": "Dashboard data"}

# Single role
@router.get("/candidate/profile")
def candidate_profile(current_user: dict = Depends(require_role(["candidate"]))):
    return {"profile": "Candidate profile"}
```

---

## 📚 Example: Protecting OA Admin Routes

Update `backend/app/routes/oa_admin.py`:

```python
from app.utils.auth_utils import get_current_recruiter

@router.post("/questions")
def create_question(
    request: CreateQuestionRequest,
    current_user: dict = Depends(get_current_recruiter)  # Add this
):
    # Only recruiters and admins can create questions
    # ... existing code ...
```

---

## 🔒 Frontend Integration

### Store Token (React/Next.js)

```javascript
// After login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();

// Store in localStorage or secure cookie
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### Make Authenticated Requests

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/candidates/1', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Check User Role

```javascript
const user = JSON.parse(localStorage.getItem('user'));

if (user.role === 'recruiter') {
  // Show recruiter dashboard
} else if (user.role === 'candidate') {
  // Show candidate dashboard
}
```

---

## 🧪 Testing with FastAPI Docs

1. Go to http://localhost:8000/docs
2. Click **"Authorize"** button (green lock icon)
3. Enter: `Bearer YOUR_TOKEN_HERE`
4. Click "Authorize"
5. All protected endpoints will now work!

---

## 🎯 Role-Based UI Flow

### Candidate Flow:
1. Register as `candidate`
2. Login → Get token
3. Access:
   - `/oa/*` - Take assessments
   - `/oa/candidate/{id}/results` - View results

### Recruiter Flow:
1. Register as `recruiter` (must provide company_name)
2. Login → Get token
3. Access:
   - `/jobs` - Create job postings
   - `/candidates` - View candidates
   - `/oa/admin/*` - Create questions, view results
   - `/candidates/{id}/send-oa` - Send OA invitations

### Admin Flow:
1. Access all routes
2. Manage users, questions, jobs

---

## 🔐 Security Best Practices

### 1. Use Environment Variables for Secrets

```python
# backend/app/utils/auth_utils.py
from app.core.config import settings

SECRET_KEY = settings.jwt_secret_key  # From .env
```

### 2. Update Config

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
```

### 3. HTTPS Only in Production

```python
# main.py - for production
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)
```

---

## 📊 Database Schema

```sql
users
├── id (INT, PK)
├── email (STRING, UNIQUE)
├── password (STRING, hashed)
├── name (STRING)
├── role (STRING: candidate/recruiter/admin)
├── company_name (STRING, nullable)
├── is_active (BOOLEAN)
├── email_verified (BOOLEAN)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
└── last_login (TIMESTAMP)
```

---

## ❓ Common Issues

### Issue: "Invalid token"
- Token expired (30 min default)
- Wrong token format
- Solution: Login again to get new token

### Issue: "Access denied"
- User doesn't have required role
- Solution: Check user role with `/auth/me`

### Issue: "Email already registered"
- User exists
- Solution: Use `/auth/login` instead

---

## 🎉 Complete Example

```python
# Example: Protected recruiter-only endpoint
from fastapi import APIRouter, Depends
from app.utils.auth_utils import get_current_recruiter

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/")
def create_job(
    title: str,
    description: str,
    current_user: dict = Depends(get_current_recruiter)
):
    """Only recruiters and admins can create jobs"""
    job_id = snowflake_client.create_job(
        title=title,
        description=description,
        created_by=current_user["user_id"]
    )
    return {"job_id": job_id, "created_by": current_user["email"]}
```

---

## 📖 Next Steps

1. ✅ Run `users_table.sql` in Snowflake
2. ✅ Install dependencies: `pip install python-jose[cryptography] passlib[bcrypt]`
3. ✅ Add JWT secret to `.env`
4. ✅ Test with `/docs` or Postman
5. 🚀 Protect your routes with role-based access
6. 🎨 Build frontend login/register UI

---

Need help? Check `/docs` for interactive API testing!

