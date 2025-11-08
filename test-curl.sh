#!/bin/bash
# Test script for resume submission using curl

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://127.0.0.1:8000"
PDF_PATH="${1:-}"  # First argument or empty
JOB_ID="${2:-1}"
JOB_DESCRIPTION="${3:-Software Engineer position with experience in Python and FastAPI}"

# Check if PDF path is provided
if [ -z "$PDF_PATH" ]; then
    echo -e "${RED}Error: PDF file path is required${NC}"
    echo ""
    echo "Usage:"
    echo "  ./test-curl.sh <path_to_resume.pdf> [job_id] [job_description]"
    echo ""
    echo "Example:"
    echo "  ./test-curl.sh ~/Documents/resume.pdf 1 \"Software Engineer\""
    echo ""
    exit 1
fi

# Check if file exists
if [ ! -f "$PDF_PATH" ]; then
    echo -e "${RED}Error: PDF file not found: $PDF_PATH${NC}"
    echo ""
    echo "Please provide a valid path to a PDF file."
    exit 1
fi

# Check if file is a PDF
if [[ ! "$PDF_PATH" =~ \.pdf$ ]]; then
    echo -e "${YELLOW}Warning: File doesn't have .pdf extension${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get absolute path
PDF_ABS_PATH=$(cd "$(dirname "$PDF_PATH")" && pwd)/$(basename "$PDF_PATH")

echo -e "${GREEN}Testing Resume Submission${NC}"
echo "================================"
echo "PDF File: $PDF_ABS_PATH"
echo "Job ID: $JOB_ID"
echo "Job Description: $JOB_DESCRIPTION"
echo "Endpoint: $BASE_URL/candidates/ingest"
echo ""

# Make the request
echo -e "${YELLOW}Sending request...${NC}"
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/candidates/ingest" \
  -F "file=@$PDF_ABS_PATH" \
  -F "job_id=$JOB_ID" \
  -F "job_description=$JOB_DESCRIPTION")

# Split response and status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo ""
if [ "$http_code" -eq 200 ]; then
    echo -e "${GREEN}✓ Success! (HTTP $http_code)${NC}"
    echo ""
    echo "Response:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
    echo ""
    echo "Response:"
    echo "$body"
fi

