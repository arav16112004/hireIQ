#!/bin/bash
# Simple server start script
cd "$(dirname "$0")"

# Kill any existing server on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Killing existing process on port 8000..."
    kill $(lsof -ti:8000) 2>/dev/null
    sleep 1
fi

# Activate venv if it exists
if [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
fi

# Set PYTHONPATH to project root
export PYTHONPATH="$(pwd):${PYTHONPATH}"

# Run from project root
cd "$(dirname "$0")"
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
