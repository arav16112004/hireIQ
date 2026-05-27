# HireIQ — AI-Driven Hiring Platform

> End-to-end hiring pipeline that takes a candidate from **resume upload → AI fit-screening → emailed online coding assessment with browser-native proctoring → AI video interview**, all in one app.

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2015-black?logo=next.js)](https://nextjs.org/)
[![Language](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Language](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-Snowflake-29B5E8?logo=snowflake&logoColor=white)](https://www.snowflake.com/)
[![AI](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Sandbox](https://img.shields.io/badge/Code%20Execution-Judge0-1E40AF)](https://judge0.com/)

---

## Table of Contents

- [Highlights](#highlights)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Core Workflows](#core-workflows)
- [API Surface](#api-surface)
- [Data Model](#data-model)
- [Integrity / Proctoring Engine](#integrity--proctoring-engine)
- [Scripts](#scripts)
- [Roadmap](#roadmap)

---

## Highlights

- **AI resume screening** — PDFs are parsed with PyMuPDF and scored against the job description by **Gemini 2.5 Flash**, producing a 0–100 fit score, structured skills list, and professional summary.
- **Automated OA invites** — Candidates with `fit_score ≥ 85` automatically receive a branded SendGrid email with a tokenized assessment link.
- **Sandboxed coding assessments** — Code is graded by **Judge0** across **11 supported languages** (Python, JavaScript, Java, C++, C, Ruby, Go, Rust, Kotlin, Swift, TypeScript) with per-question test cases, hidden test cases, and CPU/memory limits.
- **Browser-native proctoring** — WebGazer.js + TensorFlow.js power a **6-point gaze calibration** flow and a **4-component integrity score** recalculated at **10 Hz**, persisted as `max_cheating_score` on the session.
- **AI video interview** — Gemini generates per-job interview questions; responses are evaluated for score, strengths, and improvements. Stub TTS (ElevenLabs) + talking-head video (D-ID) services produce per-question media assets.
- **Multi-tenant recruiter portal** — Recruiters see only candidates from their own company via JOINs on `jobs.company_name`.
- **Production-aware** — JWT auth (HS256, bcrypt, 24-hour tokens), 3 user roles, strict CORS allowlist, schema-evolution-tolerant SQL (probes `INFORMATION_SCHEMA` before writing newer columns).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│            Next.js 15 (App Router) — frontend/                  │
│  • Monaco editor + split-pane OA UI                             │
│  • WebGazer.js gaze tracking (6-pt calibration, 10 Hz scoring)  │
└─────────────────────────────────────────────────────────────────┘
                                │ Axios + JWT
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI — backend/app/main.py                      │
│  10 routers • 63 endpoints • role-based access control          │
└─────────────────────────────────────────────────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
   ┌────────┐    ┌─────────┐   ┌──────────┐   ┌──────────┐
   │Gemini  │    │ Judge0  │   │ SendGrid │   │Snowflake │
   │2.5     │    │ CE API  │   │ (email)  │   │   DB     │
   │Flash   │    │(sandbox)│   │          │   │ 12 tables│
   └────────┘    └─────────┘   └──────────┘   └──────────┘
```

---

## Tech Stack

| Layer       | Technology                                                                 |
| ----------- | -------------------------------------------------------------------------- |
| Frontend    | Next.js 15.5, React 19.2, TypeScript 5.6, Tailwind CSS 4.1, Axios          |
| Editor      | Monaco Editor (`@monaco-editor/react`)                                     |
| Proctoring  | WebGazer.js 3.1, TensorFlow.js 4.22, face-landmarks-detection 1.0          |
| Backend     | FastAPI 0.121+, Pydantic v2, Uvicorn, python-jose (JWT), bcrypt            |
| AI / ML     | Google Gemini 2.5 Flash (`google-genai`)                                   |
| Code sandbox| Judge0 CE (RapidAPI or self-hosted)                                        |
| Email       | SendGrid                                                                   |
| PDF parsing | PyMuPDF (`fitz`)                                                           |
| Database    | Snowflake (`snowflake-connector-python`)                                   |
| TTS / Video | ElevenLabs (TTS) + D-ID (avatar video) — pluggable service wrappers        |

---

## Project Structure

```
hireIQ/
├── backend/
│   ├── app/
│   │   ├── core/              # config, deps, logging
│   │   ├── db/                # Snowflake + OA data access layer
│   │   │   └── schemas/       # Pydantic models for jobs, candidates, OA, interviews
│   │   ├── routes/            # 10 FastAPI routers (auth, oa, jobs, candidates, ...)
│   │   ├── services/          # Gemini, Judge0, grading, OA trigger, email, TTS, D-ID
│   │   ├── utils/             # auth_utils (JWT/bcrypt), email_utils (SendGrid)
│   │   └── main.py            # FastAPI app entrypoint + CORS + static mounts
│   ├── *.sql                  # Snowflake migrations (users, candidate_profiles, OA, ...)
│   ├── tests/                 # pytest suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                   # Next.js App Router pages
│   │   ├── auth/              # login / register
│   │   ├── candidate/         # dashboard + profile
│   │   ├── recruiter/         # dashboard + candidates + jobs management
│   │   ├── oa/                # OA session UI ([sessionId]) + results
│   │   ├── integrity/         # WebGazer calibration & monitoring
│   │   ├── interview/         # AI interview entrypoint
│   │   ├── apply/             # public job application
│   │   └── jobs/              # public job listings
│   ├── components/            # Navbar, AnimatedParticles
│   ├── lib/
│   │   ├── api.ts             # Axios client with JWT interceptor
│   │   ├── auth.tsx           # React Context auth provider
│   │   └── integrity.tsx      # useIntegrityMonitor() hook
│   └── package.json
├── requirements.txt           # root convenience pin
└── START_EVERYTHING.sh        # one-command dev launcher
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Snowflake account (database + warehouse)
- A Gemini API key (free tier works)
- (Optional) SendGrid API key for real email delivery
- (Optional) Judge0 RapidAPI key, or self-host Judge0

### 1. Clone & configure

```bash
git clone https://github.com/arav16112004/hireIQ.git
cd hireIQ
cp backend/.env.example backend/.env
# Edit backend/.env with your Snowflake / Gemini / SendGrid / Judge0 credentials
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Snowflake schema scripts (in order):
#   users_table.sql, candidate_profiles.sql, oa_email_logs.sql,
#   add_company_name_to_jobs.sql, add_company_principles_to_jobs.sql,
#   add_max_cheating_score_to_oa_sessions.sql, oa_sample_data.sql

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at <http://localhost:8000> — interactive docs at <http://localhost:8000/docs>.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at <http://localhost:3000>.

### 4. Or — one-shot

```bash
./START_EVERYTHING.sh
```

Starts backend + frontend, waits for `/health`, and prints the URLs.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

```env
# Snowflake
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_DATABASE=TEAM_SERO
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=TEAM_SERO_WH

# Email
SENDGRID_API_KEY=...
SENDGRID_FROM_EMAIL=noreply@hireiq.tech

# Gemini
GEMINI_API_KEY=...

# OA
OA_THRESHOLD=0.85           # fit-score gate for auto-OA invite
OA_BASE_URL=http://localhost:3000

# Judge0
JUDGE0_URL=https://judge0-ce.p.rapidapi.com
JUDGE0_API_KEY=...
JUDGE0_RAPIDAPI_HOST=judge0-ce.p.rapidapi.com

# JWT
JWT_SECRET_KEY=change-me-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Frontend reads `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

---

## Core Workflows

### Candidate stage machine

```
applied  ──►  oa_sent  ──►  oa_passed  ──►  ai_passed  ──►  final
   │
   └── (fit_score < 85)  ──►  rejected
```

### End-to-end flow

1. **Apply** — Candidate uploads a PDF resume against a job.
2. **Screen** — PyMuPDF extracts text; Gemini 2.5 Flash returns `{skills, summary, fit_score}`.
3. **Invite** — If `fit_score ≥ 85`, SendGrid emails a tokenized OA link.
4. **Calibrate** — Candidate completes 6-point WebGazer calibration (stored in `localStorage`).
5. **Assess** — Monaco editor + 5-language switcher; submissions graded by Judge0 against visible + hidden test cases.
6. **Score** — Per-question best score is summed; session percentage written to `oa_sessions.score / max_score`, integrity score written to `oa_sessions.max_cheating_score` and `oa_results.integrity_score`.
7. **Gate** — `≥ 70%` passes the OA. `≥ 90%` unlocks the AI interview.
8. **Interview** — Gemini generates 5 questions; each response is evaluated; transcript + averaged engagement/AI scores saved.
9. **Review** — Recruiter sees candidates scoped to their company, with full audit trail (email logs, sessions, submissions, results, interviews).

---

## API Surface

10 routers / 63 endpoints. Highlights:

### Authentication (`/auth`)

| Method | Path                      | Description                          |
| ------ | ------------------------- | ------------------------------------ |
| POST   | `/auth/register`          | Register user (any role)             |
| POST   | `/auth/register/candidate`| Register a candidate                  |
| POST   | `/auth/register/recruiter`| Register a recruiter (with company)   |
| POST   | `/auth/login`             | Returns JWT bearer token             |
| GET    | `/auth/me`                | Current user info                    |
| POST   | `/auth/logout`            | Logout (client deletes token)        |

### Candidates (`/candidates`)

| Method | Path                              | Description                                |
| ------ | --------------------------------- | ------------------------------------------ |
| GET    | `/candidates`                     | List (role-scoped)                         |
| POST   | `/candidates/ingest`              | Upload PDF → Gemini → fit score → auto-OA  |
| GET    | `/candidates/{id}`                | Candidate detail                           |
| DELETE | `/candidates/{id}`                | Delete (recruiter/admin only)              |
| POST   | `/candidates/{id}/send-oa`        | Manually trigger OA invite                 |
| GET    | `/candidates/{id}/email-logs`     | Per-candidate email audit                  |
| POST   | `/candidates/match`               | AI rank jobs for candidate                 |

### Online Assessment (`/oa`)

| Method | Path                                  | Description                                     |
| ------ | ------------------------------------- | ----------------------------------------------- |
| POST   | `/oa/access`                          | Public token verification from email link       |
| GET    | `/oa/my-sessions`                     | Current user's OA sessions                      |
| POST   | `/oa/start`                           | Start a new OA session                          |
| GET    | `/oa/session/{id}`                    | Session + questions (auto-starts pending)       |
| POST   | `/oa/submit`                          | Submit code → Judge0 → graded synchronously     |
| GET    | `/oa/submission/{id}`                 | Submission details + test case results          |
| GET    | `/oa/session/{id}/results`            | Aggregated session results                      |
| POST   | `/oa/complete`                        | Finalize session + write `max_cheating_score`   |
| GET    | `/oa/candidate/{id}/results`          | Full OA history for a candidate                 |
| GET    | `/oa/languages`                       | Judge0 language map                             |

### OA Admin (`/oa/admin`) — 11 endpoints

Full CRUD for `oa_questions`, `oa_test_cases`, and a sessions overview.

### Interviews (`/interviews`)

| Method | Path                       | Description                                    |
| ------ | -------------------------- | ---------------------------------------------- |
| GET    | `/interviews/eligibility`  | OA score ≥ 90% gate                            |
| POST   | `/interviews/start`        | Gemini-generated questions, in-memory session  |
| POST   | `/interviews/next`         | Submit response, get evaluation + next Q + TTS |
| POST   | `/interviews/end`          | Save transcript + scores to Snowflake          |
| POST   | `/interviews/metrics/eye`  | Submit gaze metrics for the interview          |

Full reference: <http://localhost:8000/docs>.

---

## Data Model

12 Snowflake tables in `TEAM_SERO.PUBLIC`:

| Table                | Purpose                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| `users`              | Auth + RBAC (`candidate` / `recruiter` / `admin`)                       |
| `candidate_profiles` | Persistent candidate info (skills `ARRAY`, resume URL, links, bio)      |
| `candidates`         | Per-application records (`fit_score`, `stage`, `job_id`)                |
| `jobs`               | Job postings (`company_name`, `company_principles`)                     |
| `oa_questions`       | Coding question bank                                                    |
| `oa_test_cases`      | Visible + hidden test cases per question                                |
| `oa_sessions`        | Per-candidate assessment instances (`score`, `max_cheating_score`)      |
| `oa_submissions`     | Graded code attempts (stdout, stderr, time, memory, `test_results` JSON)|
| `oa_results`         | Aggregate per-candidate OA outcome (`integrity_score`)                  |
| `oa_email_logs`      | SendGrid delivery audit (`sent` / `failed` / `bounced`)                 |
| `interviews`         | AI interview transcript + scores                                        |
| `final_interviews`   | Recruiter decision tracking                                             |

Schemas live in `backend/*.sql` and are designed to be re-runnable.

---

## Integrity / Proctoring Engine

A 100% client-side proctoring system powered by WebGazer.js — **no server-side video, no streaming**, just a live integrity score.

- **6-point calibration** — user clicks each red dot while looking at it; calibration data persists in `localStorage`.
- **10 Hz scoring loop** (every 100 ms) reads from a ref to avoid React re-render thrash.
- **5 gaze payload shapes** supported (WebGazer’s API is inconsistent across versions).
- **4-component score** (0–100, clamped):

  | Component                          | Weight | Trigger                                                  |
  | ---------------------------------- | -----: | -------------------------------------------------------- |
  | Immediate deviation from center    |  50 %  | 4 tiers from 0.05 → 0.4 normalized deviation             |
  | Eye-movement velocity penalty      |  20 %  | Frame-to-frame gaze delta, capped at 30                  |
  | Historical off-center glance ratio |  10 %  | Rolling 100-tick window with exponential decay           |
  | Time-based penalty                 |  20 %  | Looking up > 4 s **or** looking down > 3 s, escalating   |

- **Session max** is the value persisted to `oa_sessions.max_cheating_score` and `oa_results.integrity_score`.
- **DOM cleanup** — periodic sweep hides any stray high-z-index gaze artifacts that WebGazer may leave behind.

---

## Scripts

| Command                                                | Description                              |
| ------------------------------------------------------ | ---------------------------------------- |
| `./START_EVERYTHING.sh`                                | Kill ports → start backend + frontend    |
| `cd backend && uvicorn app.main:app --reload`          | Backend dev server                       |
| `cd backend && pytest`                                 | Run backend tests                        |
| `cd frontend && npm run dev`                           | Frontend dev server                      |
| `cd frontend && npm run build && npm start`            | Frontend production build                |
| `cd frontend && npm run lint`                          | ESLint                                   |

---

## Roadmap

- [ ] Persist Judge0 submission tokens for async grading (currently synchronous)
- [ ] Replace in-memory interview session store with Redis
- [ ] Real ElevenLabs + D-ID integration (currently stubs writing placeholder assets)
- [ ] Per-question analytics dashboard for recruiters
- [ ] Multi-language test harness (currently Python-only auto-wrap)
- [ ] Webhook-based SendGrid open/click tracking
- [ ] Containerized self-hosted Judge0 for production

