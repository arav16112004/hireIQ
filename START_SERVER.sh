#!/bin/bash
# Simple script to start the FastAPI server

echo "🚀 Starting FastAPI Server..."
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo "❌ Virtual environment not found at backend/.venv"
    echo "Please create it first:"
    echo "  cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source backend/.venv/bin/activate

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="$(pwd):${PYTHONPATH}"

echo "🌐 Starting server on http://127.0.0.1:8000"
echo "📚 API docs: http://127.0.0.1:8000/docs"
echo "🏥 Health check: http://127.0.0.1:8000/health"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

