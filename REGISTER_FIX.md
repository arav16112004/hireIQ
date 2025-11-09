# Registration Error Fix

## Problem
Backend returns "Internal Server Error" when trying to register.

## Solution

**Restart the backend server in a NEW terminal** (not background) so you can see the actual error:

```bash
# Terminal 1: Backend (watch for errors)
cd backend
source .venv/bin/activate  
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Terminal 2: Frontend
cd frontend
npm run dev
```

Then try to register and **look at Terminal 1** to see the actual error message.

## Common Issues

1. **Missing `users` table in Snowflake**
   - Run: `backend/users_table.sql` in Snowflake

2. **Wrong password field name**
   - Check if table uses `PASSWORD` or `PASSWORD_HASH`

3. **Database connection failed**
   - Check Snowflake credentials in `backend/.env`

## Quick Test

Test registration directly:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123456","name":"Test","role":"candidate"}'
```

If you see the actual error in Terminal 1, that will tell us what's wrong!

