#!/bin/bash
# Fix PDF import error by installing the correct PyMuPDF package

echo "🔧 Fixing PDF import error..."
echo ""

cd "$(dirname "$0")/backend"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please create it first."
    exit 1
fi

# Uninstall conflicting fitz package if it exists
echo "📦 Uninstalling conflicting 'fitz' package..."
pip uninstall -y fitz 2>/dev/null || echo "   (no conflicting package found)"

# Install PyMuPDF (the correct package)
echo "📦 Installing PyMuPDF..."
pip install PyMuPDF>=1.23.0

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python -c "import fitz; print('✅ PyMuPDF installed successfully')" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Fixed! PyMuPDF is now correctly installed."
    echo ""
    echo "You can now start the server:"
    echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
else
    echo ""
    echo "❌ Installation failed. Please check the error above."
    exit 1
fi

