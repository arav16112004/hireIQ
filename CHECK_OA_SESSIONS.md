# Quick Check: Why OA Sessions Aren't Showing

## Step 1: Check Browser Console
1. Open browser console (F12)
2. Look for `=== OA SESSIONS API RESPONSE ===`
3. Check what `Message:` says - this will tell you the issue

## Step 2: Check Backend Logs
Look for these logs in your backend terminal:
- `=== FETCHING OA SESSIONS ===`
- `User email: arav4mehta@gmail.com`
- `✅ Found candidate_id: X` OR `❌ No candidate record found`
- `Sessions count: X`

## Common Issues:

### Issue 1: "No candidate record found"
**Cause:** Your email `arav4mehta@gmail.com` doesn't exist in the `CANDIDATES` table
**Solution:** You need to apply for a job first to create a candidate record

### Issue 2: Candidate found but no sessions
**Cause:** Candidate exists but no OA sessions have been created
**Solution:** 
- Check if OA was triggered for this candidate
- Check backend logs for "Created OA session" messages
- Verify sessions exist in database: `SELECT * FROM OA_SESSIONS WHERE CANDIDATE_ID = <your_candidate_id>`

### Issue 3: Sessions exist but for different candidate_id
**Cause:** OA sessions were created for a different candidate_id than your account
**Solution:** Check what candidate_id your email maps to vs what candidate_id has sessions

## Quick Database Check:
Run this in Snowflake to check:
```sql
-- Check if candidate exists
SELECT * FROM CANDIDATES WHERE UPPER(EMAIL) = UPPER('arav4mehta@gmail.com');

-- Check OA sessions for that candidate
SELECT * FROM OA_SESSIONS WHERE CANDIDATE_ID = <candidate_id_from_above>;

-- Check all OA sessions
SELECT CANDIDATE_ID, COUNT(*) as session_count 
FROM OA_SESSIONS 
GROUP BY CANDIDATE_ID;
```

