# Testing Guide for Resume Submission

## Step 1: Start the FastAPI Server

```bash
# Navigate to project root
cd /Users/arav/Desktop/teamsero

# Start the server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Or if you're in the backend directory:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 2: Verify Server is Running

### Option A: Use the Test Script (PowerShell)
```powershell
.\test-endpoint.ps1
```

### Option B: Manual Test (Browser/curl)
- Open browser: http://127.0.0.1:8000/health
- Or use curl: `curl http://127.0.0.1:8000/health`

You should see: `{"status":"healthy"}`

## Step 3: Submit a Resume

### Option A: PowerShell Script (Recommended)
```powershell
# Load the function
. .\test-resume-submit.ps1

# Submit a resume
Submit-Resume -PdfPath "C:\path\to\your\resume.pdf" -JobDescription "Software Engineer position with experience in Python and FastAPI" -JobId 1
```

### Option B: Using curl (Mac/Linux)
```bash
# Make sure to use the FULL path to your PDF file
# Replace /path/to/resume.pdf with the actual path to your PDF

curl -X POST "http://127.0.0.1:8000/candidates/ingest" \
  -F "file=@/full/path/to/your/resume.pdf" \
  -F "job_id=1" \
  -F "job_description=Software Engineer position with experience in Python and FastAPI"

# Or use the test script (easier):
./test-curl.sh /path/to/resume.pdf 1 "Software Engineer position"
```

### Option C: FastAPI Interactive Docs (Easiest!)
1. Open browser: http://127.0.0.1:8000/docs
2. Find the `/candidates/ingest` endpoint
3. Click "Try it out"
4. Upload a PDF file
5. Fill in `job_id` (e.g., `1`)
6. Fill in `job_description` (e.g., "Software Engineer")
7. Click "Execute"

## Step 4: Check Response

You should receive a JSON response like:
```json
{
  "candidate_id": 123,
  "fit_score": 85.5,
  "skills": ["Python", "FastAPI", "Docker"],
  "summary": "Candidate has strong experience in...",
  "status": "accepted"
}
```

## Troubleshooting

### Server won't start?
- Check if port 8000 is already in use
- Verify your `.env` file is in `backend/.env`
- Check Python dependencies: `pip install -r backend/requirements.txt`

### PDF upload fails?
- Ensure the file is a valid PDF
- Check file path is correct
- Verify the server is running

### API returns error?
- Check server logs for detailed error messages
- Verify Snowflake connection in `.env`
- Check Gemini API key is set

## Test Endpoints

- Health: http://127.0.0.1:8000/health
- Root: http://127.0.0.1:8000/
- API Docs: http://127.0.0.1:8000/docs
- Gemini Test: http://127.0.0.1:8000/candidates/test-gemini

