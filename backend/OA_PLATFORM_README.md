# 🧪 TeamSero OA Platform - Complete Setup Guide

## ✅ What's Built

### 1. **Database (Snowflake)**
- ✅ 4 tables: `oa_questions`, `oa_test_cases`, `oa_sessions`, `oa_submissions`
- ✅ 5 medium-level coding questions with test cases
- ✅ Integrated with main `candidates` table

### 2. **Services**
- ✅ `judge0_service.py` - Judge0 CE API integration for code execution
- ✅ `grading_service.py` - Auto-grading with database updates
- ✅ `oa_client.py` - Snowflake OA database functions

### 3. **API Routes**
- ✅ `/oa/*` - Candidate-facing endpoints (10 routes)
- ✅ `/oa/admin/*` - Admin endpoints (9 routes)

---

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd backend
.venv/bin/pip install requests
```

### 2. Configure Environment Variables

Add to `backend/.env`:

```env
# Judge0 Configuration (RapidAPI)
JUDGE0_URL=https://judge0-ce.p.rapidapi.com
JUDGE0_API_KEY=your_rapidapi_key_here
JUDGE0_RAPIDAPI_HOST=judge0-ce.p.rapidapi.com
```

**Get Judge0 API Key:**
1. Go to https://rapidapi.com/judge0-official/api/judge0-ce
2. Subscribe to free tier (350 requests/month)
3. Copy your API key

### 3. Run Snowflake SQL Scripts

Already done:
- ✅ Tables created
- ✅ Sample questions inserted

### 4. Start the Server

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

---

## 📚 API Endpoints

### **Candidate Endpoints** (`/oa/`)

#### 1. Start OA Session
```http
POST /oa/start
Content-Type: application/json

{
  "candidate_id": 1,
  "question_ids": [1, 2, 3],
  "duration_minutes": 60
}
```

**Response:**
```json
{
  "session_id": 1,
  "questions": [...],
  "started_at": "2025-11-08T12:00:00",
  "expires_at": "2025-11-08T13:00:00"
}
```

#### 2. Submit Code
```http
POST /oa/submit
Content-Type: application/json

{
  "session_id": 1,
  "question_id": 1,
  "source_code": "def two_sum(nums, target):\n    ...",
  "language": "python"
}
```

**Response:**
```json
{
  "submission_id": 1,
  "status": "pending",
  "message": "Code submitted successfully. Grading in progress..."
}
```

#### 3. Get Submission Result
```http
GET /oa/submission/{submission_id}
```

**Response:**
```json
{
  "submission_id": 1,
  "status": "completed",
  "score": 75,
  "passed_tests": 3,
  "total_tests": 4,
  "execution_time": 0.032,
  "stdout": "...",
  "test_results": {...}
}
```

#### 4. Complete Session
```http
POST /oa/complete
Content-Type: application/json

{
  "session_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "candidate_id": 1,
  "total_score": 225,
  "max_score": 300,
  "percentage": 75,
  "passed": true,
  "new_stage": "oa_passed"
}
```

#### 5. Get Candidate Results
```http
GET /oa/candidate/{candidate_id}/results
```

### **Admin Endpoints** (`/oa/admin/`)

#### 1. List All Questions
```http
GET /oa/admin/questions?active_only=true
```

#### 2. Create Question
```http
POST /oa/admin/questions
Content-Type: application/json

{
  "title": "Reverse String",
  "description": "Write a function to reverse a string...",
  "difficulty": "medium",
  "language": "python",
  "points": 100,
  "test_cases": [
    {
      "input": "hello",
      "expected_output": "olleh",
      "is_hidden": false,
      "points": 50
    }
  ]
}
```

#### 3. Get Question Stats
```http
GET /oa/admin/stats
```

**Response:**
```json
{
  "total_questions": 5,
  "easy": 0,
  "medium": 5,
  "hard": 0,
  "active": 5
}
```

#### 4. Get Session Detailed Report
```http
GET /oa/admin/sessions/{session_id}/detailed
```

---

## 🔄 Complete Flow

### 1. **Recruiter Creates Job & Uploads Resume**
```
POST /jobs → Job created
POST /candidates → Candidate created with job_id
```

### 2. **AI Screens Resume (Your existing flow)**
```
Gemini analyzes → fit_score calculated → saved to candidates table
```

### 3. **OA Trigger (if fit_score ≥ 70%)**
```python
from app.services.oa_trigger import trigger_oa_for_candidate

result = trigger_oa_for_candidate(candidate_id=1)
# Sends email with OA link
```

### 4. **Candidate Takes OA**
```
POST /oa/start → Session started
GET /oa/question/{id} → Get question details
POST /oa/submit → Submit code (Judge0 grades it)
GET /oa/submission/{id} → Check results
POST /oa/complete → Finalize session
```

### 5. **Results Updated Automatically**
```
grading_service.complete_oa_session_with_results()
  ↓
Updates oa_sessions table with score
  ↓
Updates candidates table:
  - score ≥ 70% → stage = "oa_passed"
  - score < 70% → stage = "oa_sent"
```

### 6. **Recruiter Views Results**
```
GET /oa/candidate/{id}/results
  ↓
Shows all sessions, submissions, scores
```

---

## 🎯 Candidate Stage Flow

```
applied → oa_sent → oa_passed → ai_passed → final
   ↑         ↑          ↑
   |         |          |
Resume  OA Trigger  OA Complete
Screen  (70% fit)   (70% score)
```

---

## 🧪 Testing the Platform

### Quick Test:

1. **Create a test candidate:**
```bash
# In Snowflake:
INSERT INTO candidates (name, email, resume_url, job_id, fit_score, stage)
VALUES ('Test User', 'test@example.com', 'http://resume.pdf', 1, 0.85, 'applied');
```

2. **Start OA session:**
```bash
curl -X POST http://localhost:8000/oa/start \
  -H "Content-Type: application/json" \
  -d '{"candidate_id": 1, "question_ids": [1, 2], "duration_minutes": 60}'
```

3. **Submit a solution:**
```bash
curl -X POST http://localhost:8000/oa/submit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "question_id": 1,
    "source_code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target - num], i]\n        seen[num] = i",
    "language": "python"
  }'
```

4. **Check result:**
```bash
curl http://localhost:8000/oa/submission/1
```

---

## 📊 Supported Languages

- Python (71)
- JavaScript (63)
- Java (62)
- C++ (54)
- C (50)
- Ruby (72)
- Go (60)
- Rust (73)
- Kotlin (78)
- Swift (83)
- TypeScript (74)

---

## 🔒 Security Notes

- Hidden test cases are never sent to candidates
- Starter code provided for each question
- Time & memory limits enforced by Judge0
- Execution happens in isolated Judge0 containers

---

## 🐛 Troubleshooting

### Judge0 Connection Issues:
- Verify API key is correct in `.env`
- Check RapidAPI subscription status
- Ensure `requests` package is installed

### Database Errors:
- Verify Snowflake credentials in `.env`
- Check tables exist: `SHOW TABLES LIKE 'oa_%';`
- Ensure network access to Snowflake

### Import Errors:
- Make sure all dependencies installed: `pip install -r requirements.txt`
- Verify `.venv` is activated

---

## 📝 Next Steps

1. ✅ Test the API endpoints
2. ✅ Integrate OA trigger with your AI resume screening
3. ✅ Build frontend UI for candidates
4. Add more questions to the bank
5. Implement anti-cheat measures (WebGazer.js)
6. Add email notifications for OA completion

---

## 💡 Tips

- **Best score per question** is used (multiple attempts allowed)
- **Passing threshold**: 70% (customizable in grading_service.py)
- **Judge0 rate limits**: 350 requests/month on free tier
- **Test cases**: Mix visible (for debugging) and hidden (for grading)

---

Need help? Check the FastAPI docs at http://localhost:8000/docs

