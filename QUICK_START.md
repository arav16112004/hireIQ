# 🚀 Quick Start Guide

## Step 1: Start the Server

**Option A: Use the start script (Easiest)**
```bash
./START_SERVER.sh
```

**Option B: Manual start**
```bash
# Make sure you're in the project root
cd /Users/arav/Desktop/teamsero

# Activate virtual environment
source backend/.venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$(pwd):${PYTHONPATH}"

# Start server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 2: Verify Server is Running

Open in browser: **http://127.0.0.1:8000/health**

Or use curl:
```bash
curl http://127.0.0.1:8000/health
```

You should see: `{"status":"healthy"}`

## Step 3: Test the API

### Option 1: Use FastAPI Docs (Recommended!)
1. Open: **http://127.0.0.1:8000/docs**
2. Find `/candidates/ingest`
3. Click "Try it out"
4. Upload a PDF
5. Fill in the form
6. Click "Execute"

### Option 2: Use curl
```bash
# Make sure you have a PDF file
./test-curl.sh /path/to/resume.pdf 1 "Software Engineer"
```

### Option 3: Use Python script
```bash
python test_resume_submit.py /path/to/resume.pdf 1 "Software Engineer"
```

## Troubleshooting

### Server won't start?
```bash
# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill

# Check if dependencies are installed
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Connection refused error?
- Make sure the server is actually running
- Check the terminal for error messages
- Verify port 8000 is not blocked by firewall

### Module import errors?
- Make sure you're running from project root
- Check that PYTHONPATH is set correctly
- Verify all dependencies are installed

## Quick Check Commands

```bash
# Check if server is running
curl http://127.0.0.1:8000/health

# Check what's on port 8000
lsof -i:8000

# Kill process on port 8000
lsof -ti:8000 | xargs kill
```

## Success Indicators

✅ Server started: You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

✅ Server is healthy: `curl http://127.0.0.1:8000/health` returns `{"status":"healthy"}`

✅ API docs available: Open http://127.0.0.1:8000/docs in browser

