# Debugging OA Sessions in Dashboard

## How to Check if OA Sessions Show Up

### 1. Check Browser Console
Open browser DevTools (F12) and look for:
- `OA sessions response:` - Shows the API response
- `Failed to fetch OA sessions:` - Shows any errors
- `OA sessions message:` - Shows backend messages

### 2. Check Backend Logs
Look for:
- `Fetching OA sessions for user email: <email>`
- `Found candidate_id: <id> for email: <email>`
- `Found <count> OA sessions for candidate <id>`
- `No candidate record found for email: <email>` - This means user hasn't applied yet

### 3. Test the API Endpoint Directly

```bash
# Get your auth token from browser localStorage
# Then test the endpoint:
curl -X GET "http://localhost:8000/oa/my-sessions" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### 4. Common Issues

#### Issue: "No candidate record found"
**Cause:** User email doesn't exist in CANDIDATES table
**Solution:** User needs to apply for a job first

#### Issue: 404 Error
**Causes:**
- Session doesn't exist in database
- Route `/oa/[sessionId]` not found
- Session ID is invalid

**Check:**
1. Verify session exists: `SELECT * FROM OA_SESSIONS WHERE ID = <session_id>`
2. Verify candidate_id matches: `SELECT * FROM CANDIDATES WHERE EMAIL = '<user_email>'`
3. Check Next.js route exists: `frontend/app/oa/[sessionId]/page.tsx`

#### Issue: Sessions Not Showing
**Causes:**
- API endpoint returning empty array
- Email case mismatch
- Frontend not parsing response correctly

**Check:**
1. Browser console for API response
2. Backend logs for candidate lookup
3. Database for sessions: `SELECT * FROM OA_SESSIONS WHERE CANDIDATE_ID = <candidate_id>`

### 5. Database Queries to Debug

```sql
-- Check if candidate exists
SELECT * FROM CANDIDATES WHERE UPPER(EMAIL) = UPPER('user@example.com');

-- Check OA sessions for candidate
SELECT * FROM OA_SESSIONS WHERE CANDIDATE_ID = <candidate_id> ORDER BY CREATED_AT DESC;

-- Check all OA sessions
SELECT * FROM OA_SESSIONS ORDER BY CREATED_AT DESC;
```

### 6. Frontend Debug Info

In development mode, the dashboard shows:
- User Email
- Sessions Count
- Data Loading status

Check the "No assessments yet" section for debug info.

