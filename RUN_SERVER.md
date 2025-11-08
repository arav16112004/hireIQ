# How to Run the Server

## Problem
The error `ModuleNotFoundError: No module named 'backend'` happens when Python can't find the module path.

## Solution: Choose the correct method based on where you are

### Method 1: From Project Root (Recommended)
```bash
# Make sure you're in /Users/arav/Desktop/teamsero
cd /Users/arav/Desktop/teamsero

# Activate virtual environment
source backend/.venv/bin/activate

# Set PYTHONPATH (important!)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 2: From Backend Directory (Simpler)
```bash
# Navigate to backend directory
cd /Users/arav/Desktop/teamsero/backend

# Activate virtual environment
source .venv/bin/activate

# Run server (note: use 'app.main:app' not 'backend.app.main:app')
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Use the Start Script
```bash
# From project root
./start-server.sh
```

## Quick Fix for Current Session

If you're currently in the backend directory:

```bash
# You're probably here: /Users/arav/Desktop/teamsero/backend
# Run this:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Why This Happens

- When you run `uvicorn backend.app.main:app`, Python looks for a `backend` module
- If you're IN the backend directory, Python can't find `backend` (because you're already inside it)
- Solution: Either run from project root OR use `app.main:app` when in backend directory

## Verify It's Working

Once started, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Then visit: http://127.0.0.1:8000/docs

