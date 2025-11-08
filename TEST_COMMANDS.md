# Quick Test Commands

## Step 1: Fix PDF Import (if needed)
```bash
cd backend
source .venv/bin/activate
pip uninstall -y fitz
pip install PyMuPDF
```

## Step 2: Start the Server
```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 3: Test the Endpoint

### Option A: Use FastAPI Docs (Easiest!)
Open in browser: **http://127.0.0.1:8000/docs**

Then:
1. Find `/candidates/ingest` endpoint
2. Click "Try it out"
3. Upload a PDF file
4. Fill in `job_id` (e.g., `1`)
5. Fill in `job_description` (e.g., `Software Engineer`)
6. Click "Execute"

### Option B: Use curl
```bash
curl -X POST "http://127.0.0.1:8000/candidates/ingest" \
  -F "file=@/path/to/your/resume.pdf" \
  -F "job_id=1" \
  -F "job_description=Software Engineer position"
```

### Option C: Use Python script
```bash
python test_resume_submit.py /path/to/resume.pdf 1 "Software Engineer"
```

## Quick Health Check
```bash
curl http://127.0.0.1:8000/health
```

Should return: `{"status":"healthy"}`

