# Debugging OA Scores - Quick Reference

## Database Fields to Update

To manually set an OA score to 95%, update the following in your database:

### Option 1: Update OA_SESSIONS table (Recommended)
```sql
UPDATE OA_SESSIONS 
SET 
    SCORE = 95,           -- Your score (can be raw points or percentage)
    MAX_SCORE = 100,      -- Maximum possible score
    STATUS = 'completed'  -- Must be 'completed' (case-insensitive)
WHERE 
    CANDIDATE_ID = <your_candidate_id>;
    -- OR WHERE ID = <session_id>;
```

### Option 2: Update OA_RESULTS table
```sql
UPDATE OA_RESULTS 
SET 
    SCORE = 95,           -- Percentage (0-100)
    STATUS = 'completed'  -- Must be 'completed'
WHERE 
    CANDIDATE_ID = <your_candidate_id>;
```

## Important Notes:

1. **OA_SESSIONS takes priority** - The code checks OA_SESSIONS first, then OA_RESULTS
2. **STATUS must be 'completed'** - The eligibility check only looks at completed sessions
3. **SCORE vs MAX_SCORE** - If SCORE=95 and MAX_SCORE=100, percentage = 95%
4. **Case sensitivity** - STATUS can be 'completed' or 'COMPLETED' (case-insensitive check)

## Verify Your Changes:

1. Check backend logs when accessing `/interviews/eligibility`:
   - Look for: `🔍 Checking OA scores for candidate X`
   - Look for: `Session X: status=..., score=..., max_score=...`
   - Look for: `✅ Best OA score for candidate X: 95.00%`

2. Check the results page:
   - Should show 95% if SCORE=95 and MAX_SCORE=100
   - Backend logs will show: `Using session SCORE/MAX_SCORE: 95.0/100.0 = 95.00%`

## Common Issues:

- **Score showing 0%**: 
  - Check if STATUS is 'completed'
  - Check if SCORE and MAX_SCORE are both set (not NULL)
  - Check if MAX_SCORE > 0

- **Interview not showing**:
  - Score must be >= 90% (not just > 90%)
  - Session must be completed
  - Refresh the dashboard after updating database

