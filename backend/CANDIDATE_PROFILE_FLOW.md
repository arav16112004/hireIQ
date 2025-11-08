# 👤 Candidate Profile System - Complete Flow

## ✅ What's Implemented:

Your candidates now have **persistent profiles** - they upload their resume once and apply to multiple jobs!

---

## 📋 Database Tables:

### 1. **`users`** - Authentication
- Who can login
- Email, password, role

### 2. **`candidate_profiles`** - Persistent Profile
- Resume URL (stored permanently!)
- Phone, location, skills, etc.
- One profile per candidate

### 3. **`candidates`** - Job Applications
- Links profile to specific jobs
- Tracks hiring pipeline per job
- Multiple entries per user (one per job application)

---

## 🔄 Complete User Flow:

### Step 1: Sign Up

```bash
POST /auth/register/candidate
{
  "email": "john@example.com",
  "password": "password123",
  "name": "John Doe"
}

# Response:
{
  "message": "Candidate account created successfully",
  "user_id": 1,
  "profile_id": 1,
  "role": "candidate",
  "next_step": "Complete your profile at /candidate/profile"
}
```

✅ **Creates**:
- User account (can login)
- Empty profile (ready to fill)

---

### Step 2: Complete Profile (Upload Resume)

```bash
PUT /candidate/profile
Authorization: Bearer <token>
{
  "resume_url": "https://bucket.s3.amazonaws.com/john-resume.pdf",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "skills": "Python, JavaScript, React, FastAPI",
  "experience_years": 3,
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "education": "BS Computer Science - Stanford",
  "bio": "Full-stack developer passionate about AI"
}

# Response:
{
  "message": "Profile updated successfully",
  "user_id": 1
}
```

✅ **Resume is now stored permanently!**

---

### Step 3: Check Profile Completion

```bash
GET /candidate/profile/check-completion
Authorization: Bearer <token>

# Response:
{
  "profile_exists": true,
  "is_complete": true,
  "missing_fields": [],
  "profile": {
    "has_resume": true,
    "has_phone": true,
    "has_location": true,
    "has_skills": true,
    "has_linkedin": true
  }
}
```

---

### Step 4: View My Profile

```bash
GET /candidate/profile
Authorization: Bearer <token>

# Response:
{
  "id": 1,
  "user_id": 1,
  "resume_url": "https://bucket.s3.amazonaws.com/john-resume.pdf",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "skills": "Python, JavaScript, React, FastAPI",
  "experience_years": 3,
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "portfolio_url": null,
  "education": "BS Computer Science - Stanford",
  "bio": "Full-stack developer passionate about AI",
  "is_profile_complete": true,
  "created_at": "2025-11-08 12:00:00",
  "updated_at": "2025-11-08 12:05:00"
}
```

---

### Step 5: Apply to Jobs (Uses Existing Profile!)

**Now when they apply to jobs, they DON'T upload resume again!**

```bash
POST /jobs/42/apply
Authorization: Bearer <token>

# Automatically uses their stored resume!
# Creates entry in 'candidates' table linking to job
```

---

## 🎨 Frontend Flow:

### After Registration:

```javascript
// 1. User registers
const response = await fetch('/auth/register/candidate', {
  method: 'POST',
  body: JSON.stringify({ email, password, name })
});

// 2. Show onboarding: "Complete your profile"
router.push('/onboarding/profile');

// 3. Profile completion form
const updateProfile = async (profileData) => {
  await fetch('/candidate/profile', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      resume_url: uploadedResumeUrl,  // Upload to S3 first
      phone,
      location,
      skills,
      experience_years,
      linkedin_url,
      education,
      bio
    })
  });
  
  // Profile complete! Show dashboard
  router.push('/candidate/dashboard');
};
```

### When Applying to Jobs:

```javascript
// Check if profile is complete
const checkProfile = async () => {
  const res = await fetch('/candidate/profile/check-completion', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await res.json();
  
  if (!data.is_complete) {
    alert('Please complete your profile first!');
    router.push('/candidate/profile/edit');
    return false;
  }
  return true;
};

// Apply to job (NO resume upload needed!)
const applyToJob = async (jobId) => {
  if (!await checkProfile()) return;
  
  await fetch(`/jobs/${jobId}/apply`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  alert('Application submitted with your saved resume!');
};
```

---

## 📊 Example UI Components:

### Profile Completion Banner:
```javascript
function ProfileCompletionBanner() {
  const [completion, setCompletion] = useState(null);
  
  useEffect(() => {
    fetch('/candidate/profile/check-completion', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(setCompletion);
  }, []);
  
  if (completion?.is_complete) return null;
  
  return (
    <div className="alert">
      <p>Complete your profile to apply to jobs!</p>
      <p>Missing: {completion?.missing_fields.join(', ')}</p>
      <Link href="/candidate/profile/edit">Complete Now</Link>
    </div>
  );
}
```

### Job Application Button:
```javascript
function ApplyButton({ jobId }) {
  const apply = async () => {
    try {
      // Just click apply - resume is already uploaded!
      await fetch(`/jobs/${jobId}/apply`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      toast.success('Applied with your saved resume!');
    } catch (error) {
      if (error.status === 400) {
        toast.error('Please complete your profile first');
        router.push('/candidate/profile/edit');
      }
    }
  };
  
  return <button onClick={apply}>Quick Apply</button>;
}
```

---

## 🔧 Setup Steps:

### 1. Run SQL Script
```bash
# In Snowflake, run:
backend/candidate_profiles.sql
```

### 2. API Already Set Up!
Routes added:
- `GET /candidate/profile` - View profile
- `PUT /candidate/profile` - Update profile
- `GET /candidate/profile/check-completion` - Check if complete
- `POST /candidate/profile/complete` - Mark as complete

### 3. Build Frontend
- Registration page
- Profile completion page
- Profile edit page
- Job listings with "Quick Apply" button

---

## ✨ Benefits:

✅ **Resume stored once** - No re-uploading  
✅ **Quick apply** - One-click application  
✅ **Profile portability** - Apply to multiple jobs  
✅ **Better UX** - Complete profile once, apply everywhere  
✅ **Data consistency** - Single source of truth  

---

## 🎯 Next: Job Application Endpoint

You'll need to create:

```python
@router.post("/jobs/{job_id}/apply")
def apply_to_job(
    job_id: int,
    current_user: dict = Depends(get_current_candidate)
):
    """Apply to a job using existing profile"""
    
    # Get candidate profile
    profile = snowflake_client.get_candidate_profile_by_user_id(
        current_user["user_id"]
    )
    
    # Check profile is complete
    if not profile or not profile.get("RESUME_URL"):
        raise HTTPException(
            status_code=400,
            detail="Please complete your profile before applying"
        )
    
    # Create candidate entry (job application)
    candidate_id = snowflake_client.create_candidate(
        name=current_user["name"],
        email=current_user["email"],
        resume_url=profile["RESUME_URL"],  # Use stored resume!
        job_id=job_id
    )
    
    return {
        "message": "Application submitted successfully",
        "candidate_id": candidate_id,
        "resume_used": profile["RESUME_URL"]
    }
```

---

**Your candidates now have persistent profiles! 🎉**

