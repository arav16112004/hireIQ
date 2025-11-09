# OA Authentication Flow Fix

## Problem Summary
When candidates received an OA (Online Assessment) link via email and clicked it, the system failed because:
1. The backend OA endpoints required authentication, but candidates weren't logged in
2. The email link format didn't match the frontend expectations
3. There was no mechanism to verify OA access without authentication
4. No redirect flow existed to bring users back to the OA after login

## Solution Overview
Implemented a comprehensive authentication flow that:
1. Allows public access verification via secure tokens
2. Prompts unauthenticated users to login
3. Redirects users back to their OA after successful authentication
4. Verifies user identity matches the intended candidate

## Changes Made

### Backend Changes

#### 1. `/backend/app/routes/oa.py`
- **Added token storage**: In-memory dictionary to store session tokens (production should use Redis/DB)
- **New public endpoints**:
  - `POST /oa/access`: Verifies candidate_id and token without authentication
  - `GET /oa/session/{session_id}/public`: Returns session info with token verification
- **Enhanced security**: Modified `GET /oa/session/{session_id}` to verify the authenticated user matches the candidate
- **Auto-start sessions**: Sessions automatically start when candidate first accesses them (changes status from "pending" to "in_progress")
- **Helper functions**:
  - `generate_oa_token()`: Creates secure tokens for OA sessions
  - `get_oa_link()`: Generates complete OA links with tokens

#### 2. `/backend/app/services/oa_trigger.py`
- **Added session creation**: `create_oa_session_for_candidate()` creates OA session when email is sent
- **Updated link generation**: `generate_oa_link()` now creates proper links with session IDs and tokens
- **Modified `trigger_oa_for_candidate()`**: Now creates the session immediately when sending email
- **Added configuration**: Default OA duration (60 min) and question IDs

### Frontend Changes

#### 3. `/frontend/lib/api.ts`
- **Added public OA endpoints**:
  - `oa.access()`: Verify candidate access with token
  - `oa.getSessionPublic()`: Get session info without auth

#### 4. `/frontend/app/oa/[sessionId]/page.tsx`
- **Complete authentication flow**:
  - Extracts `candidate_id` and `token` from URL parameters
  - Verifies access using public endpoint before requiring auth
  - Checks if user is authenticated
  - Redirects to login with return URL if not authenticated
  - Verifies logged-in user matches the candidate email
  - Shows appropriate error messages for various failure scenarios
- **Enhanced UX**: Loading states, error displays, and helpful messages

#### 5. `/frontend/lib/auth.tsx`
- **Added redirect support**: `login()` function now accepts optional `redirectUrl` parameter
- **Smart redirection**: After login, redirects to custom URL if provided, otherwise uses role-based default

#### 6. `/frontend/app/auth/login/page.tsx`
- **Redirect URL handling**: Reads `redirect` query parameter
- **Auto-redirect**: If already logged in, automatically redirects to intended destination
- **Enhanced messaging**: Shows context-aware message when redirecting for OA access

## Flow Diagram

### User Flow: Accessing OA from Email

```
1. User clicks OA link from email
   → URL: /oa/123?candidate_id=456&token=abc123...

2. Frontend extracts parameters and calls public API
   → POST /oa/access { candidate_id: 456, token: "abc123..." }

3. Backend verifies token and returns session info
   ✓ Token valid? ✓ Session exists? ✓ Not expired?

4. Frontend checks authentication
   ❌ Not logged in → Redirect to /auth/login?redirect=/oa/123?candidate_id=456&token=abc123...
   ✓ Logged in → Continue to step 5

5. User logs in (or registers)
   → Login function receives redirect URL
   → After successful auth, redirects back to OA page

6. Frontend verifies user email matches candidate
   ✓ Match → Load OA session
   ❌ No match → Show error, redirect to login

7. User takes the assessment
```

## Security Features

1. **Token-based access**: Each OA link has a unique, secure token
2. **Email verification**: System verifies logged-in user's email matches the candidate
3. **Session validation**: Checks for expired or completed sessions
4. **Protected endpoints**: Main OA endpoints still require authentication
5. **Public endpoints**: Limited to access verification only, no sensitive data exposed

## Testing Checklist

### Manual Testing Steps:

1. **Send OA Email**
   ```bash
   # Use the API to send OA to a candidate
   curl -X POST http://localhost:8000/candidates/{id}/send-oa \
     -H "Authorization: Bearer {token}" \
     -d '{"force": true}'
   ```

2. **Test Unauthenticated Access**
   - Click OA link from email (while logged out)
   - Should see "Please login to continue" message
   - Should redirect to login page
   - After login, should return to OA

3. **Test Authenticated Access**
   - Log in as the candidate
   - Click OA link from email
   - Should go directly to the assessment

4. **Test Wrong User**
   - Log in as different candidate/user
   - Try to access someone else's OA link
   - Should see permission denied error

5. **Test Expired/Invalid Tokens**
   - Use invalid token in URL
   - Should see "Invalid or expired OA link" error

## Production Considerations

### Required Changes for Production:

1. **Token Storage**
   - Replace in-memory `_session_tokens` dict with Redis or database
   - Add token expiration (e.g., 7 days)
   - Implement token cleanup/garbage collection

2. **Configuration**
   - Set proper `OA_BASE_URL` in settings for production domain
   - Configure default question IDs based on job type
   - Set appropriate session durations

3. **Security Enhancements**
   - Add rate limiting on public endpoints
   - Implement CAPTCHA on login page
   - Add audit logging for OA access attempts
   - Consider adding IP restrictions

4. **Monitoring**
   - Track OA link click rates
   - Monitor authentication failures
   - Alert on suspicious access patterns

## API Documentation

### New Endpoints

#### POST /oa/access
Verify OA access from email link (no auth required)

**Request:**
```json
{
  "candidate_id": 123,
  "token": "abc123..."
}
```

**Response:**
```json
{
  "success": true,
  "session_id": 456,
  "candidate_id": 123,
  "candidate_email": "candidate@example.com",
  "candidate_name": "John Doe",
  "status": "pending",
  "message": "Access verified. Please login to continue."
}
```

#### GET /oa/session/{session_id}/public?token={token}
Get session info without authentication

**Response:**
```json
{
  "session_id": 456,
  "candidate_id": 123,
  "candidate_email": "candidate@example.com",
  "status": "pending",
  "duration_minutes": 60,
  "question_ids": [1, 2]
}
```

## Troubleshooting

### Common Issues:

1. **"Invalid or expired OA link"**
   - Token may have been cleared (server restart with in-memory storage)
   - Solution: Re-send OA email to generate new token

2. **"You don't have permission to access this assessment"**
   - User logged in with wrong account
   - Solution: Log out and log in with correct candidate email

3. **Redirect loop**
   - Check that URL parameters are preserved during redirect
   - Verify auth state is properly initialized

4. **Session not found after login**
   - Ensure session was created when email was sent
   - Check OA trigger logs for errors

## Email Link Format

Old format (broken):
```
http://localhost:3000/oa?candidate_id=123&token=xyz
```

New format (working):
```
http://localhost:3000/oa/456?candidate_id=123&token=abc123xyz...
```

Where:
- `456` is the session_id
- `123` is the candidate_id
- `abc123xyz...` is the secure access token

## Future Enhancements

1. **Magic Link Login**: Allow candidates to log in directly from the OA link
2. **Remember Device**: Skip verification on trusted devices
3. **Email Reminders**: Send reminders for incomplete OAs
4. **Session Resume**: Allow candidates to continue where they left off
5. **Mobile Optimization**: Ensure smooth mobile experience

