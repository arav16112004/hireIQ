# Quick test script to verify the API is running
param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

Write-Host "Testing API endpoints..." -ForegroundColor Cyan

# Test health endpoint
try {
    Write-Host "`n1. Testing /health endpoint..." -ForegroundColor Yellow
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Host "   ✓ Health check: $($health | ConvertTo-Json)" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Health check failed: $_" -ForegroundColor Red
    Write-Host "   Make sure the server is running: uvicorn backend.app.main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Test root endpoint
try {
    Write-Host "`n2. Testing / endpoint..." -ForegroundColor Yellow
    $root = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get
    Write-Host "   ✓ Root endpoint: $($root.message)" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Root endpoint failed: $_" -ForegroundColor Red
}

# Test candidates endpoint (should return 404 or 405 for GET, but shows endpoint exists)
try {
    Write-Host "`n3. Testing /candidates/ingest endpoint (GET - should fail)..." -ForegroundColor Yellow
    try {
        $result = Invoke-RestMethod -Uri "$BaseUrl/candidates/ingest" -Method Get -ErrorAction Stop
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 405) {
            Write-Host "   ✓ Endpoint exists (405 Method Not Allowed is expected for GET)" -ForegroundColor Green
        }
        else {
            Write-Host "   Response: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "   ✗ Endpoint test failed: $_" -ForegroundColor Red
}

# Test Gemini endpoint
try {
    Write-Host "`n4. Testing /candidates/test-gemini endpoint..." -ForegroundColor Yellow
    $gemini = Invoke-RestMethod -Uri "$BaseUrl/candidates/test-gemini" -Method Get
    Write-Host "   ✓ Gemini status: $($gemini.status)" -ForegroundColor Green
    Write-Host "   Message: $($gemini.message)" -ForegroundColor $(if ($gemini.status -eq "working") { "Green" } else { "Yellow" })
}
catch {
    Write-Host "   ✗ Gemini test failed: $_" -ForegroundColor Red
}

Write-Host "`n=== API Test Complete ===" -ForegroundColor Cyan
Write-Host "To submit a resume, use:" -ForegroundColor Yellow
Write-Host "  .\test-resume-submit.ps1 -PdfPath 'path\to\resume.pdf' -JobDescription 'Job description' -JobId 1" -ForegroundColor White

