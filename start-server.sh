#!/bin/bash
# Start script for FastAPI server
# This script handles port conflicts and starts the server correctly

PORT=8000

# Function to kill process on a port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid on port $port..."
        kill $pid
        sleep 1
    fi
}

# Check if port is in use and kill if needed
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "Port $PORT is already in use. Killing existing process..."
    kill_port $PORT
fi

# Navigate to project root
cd "$(dirname "$0")"

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found. Make sure you're in the project root."
    exit 1
fi

echo "Starting FastAPI server on port $PORT..."
echo "API docs will be available at: http://127.0.0.1:$PORT/docs"
echo ""

# Set PYTHONPATH to include project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if we're in a virtual environment, if not, try to activate backend/.venv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "backend/.venv" ]; then
        echo "Activating virtual environment..."
        source backend/.venv/bin/activate
    fi
fi

# Start the server from project root
# Use python -m uvicorn to ensure proper module resolution
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port $PORT

