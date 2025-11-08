# Quick Test Guide

## 🚀 Fastest Way to Test

### 1. Make sure server is running
```bash
# From project root
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open FastAPI Docs (Easiest!)
Open in browser: **http://127.0.0.1:8000/docs**

Then:
1. Find `/candidates/ingest` endpoint
2. Click "Try it out"
3. Upload a PDF file
4. Fill in `job_id` (e.g., `1`)
5. Fill in `job_description` (e.g., `Software Engineer`)
6. Click "Execute"

### 3. Using curl (if you have a PDF file)

**Common curl errors and fixes:**

❌ **Error: "Failed to open/read local data from file"**
- **Cause:** File path is wrong or file doesn't exist
- **Fix:** Use full absolute path to the PDF file

```bash
# WRONG (relative path might not work)
curl -X POST "http://127.0.0.1:8000/candidates/ingest" \
  -F "file=@resume.pdf" \

# CORRECT (use full path)
curl -X POST "http://127.0.0.1:8000/candidates/ingest" \
  -F "file=@/Users/arav/Desktop/resume.pdf" \
  -F "job_id=1" \
  -F "job_description=Software Engineer"
```

**Use the test script instead (recommended):**
```bash
./test-curl.sh /path/to/resume.pdf 1 "Software Engineer"
```

### 4. Using Python script
```bash
python test_resume_submit.py /path/to/resume.pdf 1 "Software Engineer"
```

## 🔍 Troubleshooting

### Server not running?
```bash
# Check if server is running
curl http://127.0.0.1:8000/health

# Should return: {"status":"healthy"}
```

### File not found error?
```bash
# Check if file exists
ls -la /path/to/resume.pdf

# Get full path
realpath resume.pdf  # Linux
readlink -f resume.pdf  # Mac (if available)
```

### Port already in use?
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill
```

## ✅ Success Response

You should see:
```json
{
  "candidate_id": 123,
  "fit_score": 85.5,
  "skills": ["Python", "FastAPI", ...],
  "summary": "Candidate has strong experience...",
  "status": "accepted"
}
```

