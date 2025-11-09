# SeroHire Frontend - Next.js

Modern, responsive frontend for the SeroHire AI-powered hiring platform.

## 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── page.tsx                 # Landing page
│   ├── layout.tsx               # Root layout with auth
│   ├── auth/                    # Authentication pages
│   │   ├── login/
│   │   └── register/
│   ├── candidate/               # Candidate portal
│   │   ├── dashboard/           # Candidate dashboard
│   │   ├── apply/               # Resume submission
│   │   └── profile/             # Profile management
│   ├── recruiter/               # Recruiter portal
│   │   ├── dashboard/           # Recruiter overview
│   │   ├── candidates/          # View candidates
│   │   └── jobs/                # Manage jobs
│   ├── oa/                      # Online assessment
│   │   └── [sessionId]/         # Take assessment
│   └── admin/                   # Admin panel
│       └── oa-questions/        # Manage questions
├── components/                  # Reusable components
│   └── Navbar.tsx              # Navigation bar
├── lib/                        # Utilities
│   ├── api.ts                  # API client
│   └── auth.tsx                # Auth context
└── public/                     # Static assets
```

## 🔌 API Integration

All backend endpoints are connected through `lib/api.ts`:

### Authentication
- `/auth/register` - User registration
- `/auth/login` - User login
- `/auth/me` - Get current user

### Candidates
- `/candidates/ingest` - Submit resume
- `/candidates/{id}` - Get candidate details
- `/candidates/{id}/send-oa` - Send OA invitation

### Jobs
- `/jobs` - List all jobs
- `/jobs/match` - Match jobs to candidate
- `/jobs/match_ai` - AI-powered job matching

### Online Assessment
- `/oa/start` - Start assessment
- `/oa/submit` - Submit code
- `/oa/complete` - Finish assessment

### Recruiter/Admin
- `/oa-admin/questions` - Manage OA questions
- `/oa-admin/sessions` - View all sessions

## 🎨 Features

### Candidate Features
- ✅ Resume upload & AI parsing
- ✅ Job matching with fit scores
- ✅ Online coding assessments
- ✅ Profile management
- ✅ Application tracking

### Recruiter Features
- ✅ Dashboard with analytics
- ✅ View all candidates
- ✅ Send OA invitations
- ✅ Review assessment results
- ✅ Job management

### Admin Features
- ✅ Create/edit OA questions
- ✅ Manage test cases
- ✅ View all sessions
- ✅ System monitoring

## 🔒 Authentication

Built-in auth system with role-based access control:

```typescript
import { useAuth } from '@/lib/auth';

function MyComponent() {
  const { user, login, logout } = useAuth();
  
  if (user?.role === 'recruiter') {
    // Recruiter-only code
  }
}
```

## 🛠️ Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Context** - State management

## 📦 Build & Deploy

```bash
# Build for production
npm run build

# Start production server
npm start

# Deploy to Vercel
vercel deploy
```

## 🔗 Backend Connection

Make sure your FastAPI backend is running on `http://localhost:8000`:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## 📱 Pages

- `/` - Landing page
- `/auth/login` - Login
- `/auth/register` - Registration
- `/candidate/dashboard` - Candidate home
- `/candidate/apply` - Apply for jobs
- `/candidate/profile` - Edit profile
- `/recruiter/dashboard` - Recruiter home
- `/oa/{sessionId}` - Take assessment
- `/admin/oa-questions` - Manage questions

## 🎯 Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🤝 Contributing

1. Make changes to the frontend
2. Test with the backend running
3. Commit your changes
4. Deploy!
