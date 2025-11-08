# Fix PDF Import Error

## Problem
The error `ModuleNotFoundError: No module named 'frontend'` occurs because there's a conflicting package named `fitz` installed instead of the correct `PyMuPDF` package.

## Solution

### Step 1: Uninstall the conflicting package
```bash
cd backend
source .venv/bin/activate
pip uninstall -y fitz
```

### Step 2: Install PyMuPDF (the correct package)
```bash
pip install PyMuPDF
```

### Step 3: Verify installation
```bash
python -c "import fitz; print(fitz.__doc__)"
```

You should see PyMuPDF documentation, not an error about 'frontend'.

### Step 4: Reinstall all requirements (recommended)
```bash
pip install -r requirements.txt
```

## Why this happens
- The package name to install is `PyMuPDF`
- But you import it as `import fitz`
- There's a separate (incorrect) package called `fitz` that conflicts
- Always install `PyMuPDF`, never install `fitz` directly

## After fixing, restart the server
```bash
# Kill any running server
lsof -ti:8000 | xargs kill

# Start server again
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

