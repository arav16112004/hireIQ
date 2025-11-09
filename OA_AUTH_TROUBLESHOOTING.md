# OA Authentication Troubleshooting Guide

## Error: "Unable to Start Assessment - Failed to start assessment. Not authenticated"

### Quick Fix Steps

1. **Clear browser cache and localStorage**
   ```javascript
   // Open browser console (F12) and run:
   localStorage.clear();
   location.reload();
   ```

2. **Check browser console for detailed logs**
   - Open Developer Tools (F12)
   - Go to Console tab
   - Look for messages starting with:
     - "Auth context initializing"
     - "Fetching session"
     - "Adding auth token to request"

### Debugging Checklist

#### Step 1: Verify Token is Being Stored
```javascript
// In browser console:
console.log('Token exists:', !!localStorage.getItem('token'));
console.log('Token value:', localStorage.getItem('token'));
```

**Expected:** Should show `true` and a long JWT string

**If empty:** The login didn't properly store the token

#### Step 2: Check Auth Context State
```javascript
// Look for these console messages after login:
// ✓ "Attempting login for: <email>"
// ✓ "Login response: { access_token: '...', user: {...} }"
// ✓ "Setting token in localStorage"
// ✓ "Token set, user data: {...}"
// ✓ "Redirecting to: /oa/..."
```

**If missing any:** There's an issue with the login flow

#### Step 3: Verify API Requests Include Token
```javascript
// Look for these messages when accessing OA:
// ✓ "Adding auth token to request: /oa/session/123"
```

**If seeing "No auth token found":** The token isn't being read from localStorage

#### Step 4: Check Backend Auth
```bash
# Test if your token is valid:
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     http://localhost:8000/auth/me

# Should return:
{
  "id": 123,
  "email": "candidate@example.com",
  "name": "...",
  "role": "candidate"
}
```

### Common Issues and Solutions

#### Issue 1: Token Stored But Not Being Sent
**Symptom:** Console shows "No auth token found for request"

**Solution:**
1. Check if multiple browser tabs are open and conflicting
2. Try incognito/private window
3. Ensure localStorage isn't blocked by browser settings

#### Issue 2: Token Invalid or Expired
**Symptom:** Console shows "Authentication error - token may be invalid or expired"

**Solution:**
1. Log out and log back in
2. Check backend JWT_SECRET_KEY matches
3. Verify JWT expiration settings in backend config

#### Issue 3: Wrong User Email
**Symptom:** "You must be logged in as [email] to access this assessment"

**Solution:**
1. Log out completely
2. Log in with the correct candidate email
3. The email in your account must match the email the OA was sent to

#### Issue 4: Redirect Loop
**Symptom:** Page keeps redirecting between login and OA

**Solution:**
1. Clear localStorage: `localStorage.clear()`
2. Close all browser tabs
3. Open new tab and login fresh
4. Click OA link from email again

### Manual Testing Steps

#### Test 1: Fresh Login Flow
```bash
# 1. Send OA email (backend)
curl -X POST http://localhost:8000/candidates/1/send-oa \
  -H "Authorization: Bearer RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'

# 2. Log out of frontend (if logged in)
# 3. Click OA link from email (or use returned link)
# 4. Should redirect to login
# 5. Log in with candidate credentials
# 6. Should redirect back to OA and start assessment
```

#### Test 2: Already Logged In
```bash
# 1. Log in to frontend as candidate
# 2. Click OA link from email
# 3. Should go directly to assessment (no login prompt)
```

#### Test 3: Check Console Logs
When you click the OA link, you should see this sequence:

```
Auth context initializing - token exists: true
Fetching user profile...
User profile loaded: { id: 123, email: "...", ... }
Checking access - candidateId: 456 token: true user: true
Access verified and user loaded, fetching session
Fetching session: 789
Auth token present: true
Adding auth token to request: /oa/session/789
Session response: { session: {...}, questions: [...] }
```

### Backend Verification

#### Check if session exists:
```bash
curl http://localhost:8000/oa/admin/sessions \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

#### Check if candidate exists:
```bash
curl http://localhost:8000/candidates/CANDIDATE_ID \
  -H "Authorization: Bearer TOKEN"
```

#### Test public access endpoint:
```bash
curl -X POST http://localhost:8000/oa/access \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": 123,
    "token": "TOKEN_FROM_EMAIL_LINK"
  }'
```

### Environment Setup Checklist

- [ ] Backend server is running on http://localhost:8000
- [ ] Frontend server is running on http://localhost:3000
- [ ] `NEXT_PUBLIC_API_URL` is set correctly in frontend
- [ ] JWT_SECRET_KEY is set in backend .env
- [ ] Database/Snowflake connection is working
- [ ] CORS is configured to allow frontend origin

### Still Not Working?

#### Enable Full Debug Mode

**Backend** - Add to `.env`:
```bash
LOG_LEVEL=DEBUG
```

**Frontend** - Add to all auth-related files (temporary):
```javascript
console.log('[DEBUG] Full state:', { user, token, loading, error });
```

#### Check Network Tab
1. Open DevTools → Network tab
2. Try accessing OA
3. Look for failed requests (red)
4. Click on `/oa/session/123` request
5. Check:
   - Request Headers → should have `Authorization: Bearer ...`
   - Response → check status code and error message

#### Common Backend Issues

**401 Unauthorized:**
- Token is invalid or expired
- JWT_SECRET_KEY mismatch
- Token format wrong (should be "Bearer TOKEN")

**403 Forbidden:**
- User email doesn't match candidate email
- User role is wrong
- Session belongs to different candidate

**404 Not Found:**
- Session doesn't exist
- Session ID in URL is wrong
- Session was never created when email was sent

### Production Deployment Issues

If this works locally but not in production:

1. **Check environment variables:**
   ```bash
   # Backend
   echo $JWT_SECRET_KEY
   echo $JWT_ALGORITHM
   echo $JWT_ACCESS_TOKEN_EXPIRE_MINUTES
   
   # Frontend
   echo $NEXT_PUBLIC_API_URL
   ```

2. **Verify CORS settings:**
   ```python
   # In backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend-domain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Check HTTPS/HTTP mixing:**
   - Frontend: https://
   - Backend: https://
   - Don't mix http and https!

4. **Browser cookies/localStorage in production:**
   - Some browsers block localStorage in iframes
   - Check secure cookie settings
   - Verify same-site cookie policies

### Get More Help

If none of these solve your issue:

1. **Capture full console output:**
   - Open DevTools Console
   - Click gear icon → check "Preserve log"
   - Reproduce the issue
   - Copy all console output

2. **Capture network request:**
   - Open DevTools Network tab
   - Try to access OA
   - Right-click failed request → Copy → Copy as cURL
   - Share this command

3. **Check backend logs:**
   ```bash
   # Look at the last 100 lines of backend logs
   tail -n 100 backend/app.log
   
   # Or if using docker:
   docker logs <container-name> --tail 100
   ```

### Quick Test Script

Save this as `test_oa_auth.sh`:

```bash
#!/bin/bash

echo "Testing OA Authentication Flow"
echo "================================"

# Configuration
BACKEND_URL="http://localhost:8000"
CANDIDATE_ID=1
EMAIL="test@example.com"
PASSWORD="testpass123"

# Step 1: Register/Login
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:20}..."

# Step 2: Test auth endpoint
echo ""
echo "2. Testing /auth/me..."
ME_RESPONSE=$(curl -s -X GET "$BACKEND_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")

echo "✅ Auth working"
echo "User: $(echo $ME_RESPONSE | jq -r '.email')"

# Step 3: Send OA
echo ""
echo "3. Sending OA to candidate..."
OA_RESPONSE=$(curl -s -X POST "$BACKEND_URL/candidates/$CANDIDATE_ID/send-oa" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true}')

SESSION_ID=$(echo $OA_RESPONSE | jq -r '.session_id')
OA_LINK=$(echo $OA_RESPONSE | jq -r '.oa_link')

if [ "$SESSION_ID" = "null" ]; then
  echo "❌ Failed to send OA!"
  echo "Response: $OA_RESPONSE"
  exit 1
fi

echo "✅ OA sent successfully"
echo "Session ID: $SESSION_ID"
echo "OA Link: $OA_LINK"

# Step 4: Test session access
echo ""
echo "4. Testing session access..."
SESSION_RESPONSE=$(curl -s -X GET "$BACKEND_URL/oa/session/$SESSION_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS=$(echo $SESSION_RESPONSE | jq -r '.session.STATUS')
echo "✅ Session accessible"
echo "Status: $STATUS"

echo ""
echo "================================"
echo "All tests passed! ✅"
echo ""
echo "Now open this link in your browser:"
echo "$OA_LINK"
```

Make executable and run:
```bash
chmod +x test_oa_auth.sh
./test_oa_auth.sh
```

