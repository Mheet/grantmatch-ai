# GrantMatch AI

**🌐 Live Demo:** [https://grantmatchai.vercel.app](https://grantmatchai.vercel.app)

AI-powered grant discovery and proposal writing platform that helps nonprofits find funding opportunities and generate professional Letters of Intent in minutes, not days.

---

## 📋 The Problem

Nonprofits spend countless hours searching for grants that match their mission. Once they find opportunities, they face another bottleneck: writing compelling Letters of Intent (LOIs) that require deep knowledge of grant writing conventions, funder expectations, and persuasive storytelling.

**The typical grant discovery process:**
- Manual searches across multiple databases (Grants.gov, foundation websites, etc.)
- Reading through hundreds of eligibility requirements
- Determining fit based on gut feeling, not data
- Starting LOI drafts from scratch for each opportunity
- Missing deadlines because the research phase took too long

**The result?** Smaller nonprofits with limited capacity miss critical funding opportunities. Grant writers burn out. Good programs go unfunded.

---

## 💡 The Solution

GrantMatch AI is a full-stack platform that combines real grant data with AI-powered matching and writing assistance. Organizations create a profile once, and the system:

1. **Matches** them against hundreds of real grants using AI scoring (0-1 scale)
2. **Ranks** opportunities by fit, not just keywords
3. **Generates** professional, customized LOIs ready to send to funders
4. **Explains** why each grant is a good match with detailed reasoning

**Core workflow:**
```
Nonprofit creates profile → AI analyzes grants → Ranked matches appear → Click "Draft LOI" → Ready-to-send proposal
```

No prompt engineering. No grant writing expertise required. Just describe your mission and let the AI do the heavy lifting.

---

## ✨ Features

### For Nonprofits
- **Smart Matching**: AI scores every grant against your mission, focus areas, and budget
- **Match Reasoning**: Detailed explanations for why each grant fits (or doesn't)
- **Instant LOI Generation**: 7-section professional proposals generated in seconds
- **Deadline Awareness**: Visual urgency indicators (Due Soon, Urgent, Expired)
- **One-Click Copy**: Copy LOIs to clipboard for immediate use

### Under the Hood
- **Real Grant Data**: 127+ grants scraped from Grants.gov (and growing)
- **Async Processing**: Background AI matching with progress tracking
- **Smart Caching**: React Query prevents redundant API calls
- **Auth-Protected**: Supabase authentication with JWT tokens
- **Production-Ready**: Deployed on Render (backend) + Vercel (frontend)

---

## 🛠️ Tech Stack

### Backend
- **Python 3.14** — Latest async/await features
- **FastAPI** — High-performance async API framework
- **SQLAlchemy 2.0** — Async ORM with relationship loading
- **Alembic** — Database migrations
- **PostgreSQL** — Via Supabase connection pooler
- **Groq API** — `llama-3.3-70b-versatile` for matching + LOI generation
- **httpx** — Async HTTP client for grant scraping
- **PyJWT** — JWT token decoding for auth

### Frontend
- **React 18** — Component-based UI
- **Vite** — Lightning-fast dev server and builds
- **Tailwind CSS v3** — Utility-first styling
- **React Query (TanStack)** — Server state management + caching
- **React Router v6** — Client-side routing
- **Axios** — HTTP client with Bearer token interceptor
- **Supabase JS** — Authentication client
- **lucide-react** — Icon library

### Infrastructure
- **Supabase** — PostgreSQL database + authentication
- **Render** — FastAPI backend hosting (free tier)
- **Vercel** — React frontend hosting
- **GitHub** — Auto-deploy on push to `main`

---

## 🏗️ Architecture

```
User → Vercel (React) → Render (FastAPI) → Supabase (PostgreSQL)
                                         → Groq API (LLM)
                                         → Grants.gov API (scraping)
```

### Auth Flow
1. User signs up/in via Supabase Auth
2. Supabase returns JWT access token
3. Axios interceptor attaches `Authorization: Bearer <token>` to every request
4. FastAPI decodes JWT to identify user
5. `GET /api/organizations/me` returns org by `user_id`

### Database Schema
**4 core tables:**
- `organizations` — name, mission, focus_areas (array), location, budget_range, user_id
- `grants` — title, funder, description, amount, deadline, source_url, focus_areas
- `grant_matches` — organization_id, grant_id, score, reasoning, generated_loi
- `loi_drafts` — (legacy, superseded by `generated_loi` column)

**Key indexes:**
```sql
CREATE INDEX idx_organizations_user_id ON organizations(user_id);
CREATE INDEX idx_grant_matches_org_id ON grant_matches(organization_id);
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.14+
- Node.js 18+
- PostgreSQL (or Supabase account)
- Groq API key (free at [groq.com](https://groq.com))

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/db?ssl=require"
export GROQ_API_KEY="your_groq_key"
export FRONTEND_URL="http://localhost:5173"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install

# Create .env file
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

### Scrape Grants (Optional)
```bash
# Trigger grant scraping pipeline
curl -X POST http://localhost:8000/api/admin/scrape
```

---

## 📡 API Documentation

### Organizations
- `POST /api/organizations` — Create org profile
- `GET /api/organizations/me` — Get org by JWT user_id
- `GET /api/organizations/{id}` — Get org by ID

### Matching
- `POST /api/matches/generate/{org_id}` — Trigger AI matching (async)
- `GET /api/matches/{org_id}` — Get ranked matches with grant details

### LOI Generation
- `POST /api/loi/generate/{match_id}` — Generate + save LOI
- Returns: `{ loi: "markdown text", match_id: 123 }`

### Admin
- `POST /api/admin/scrape` — Trigger grant scraping pipeline

**Interactive docs:** Visit `http://localhost:8000/docs` for Swagger UI

---

## 🎯 How the AI Works

### Matching Engine (`backend/services/matcher.py`)
1. Fetches org profile from database
2. Queries unmatched grants (excludes already scored via `notin_` subquery)
3. For each grant:
   - Sends org + grant details to Groq
   - Receives match score (0.0 - 1.0) + reasoning paragraph
   - Saves scores above threshold (0.4) to `grant_matches`
4. Sequential processing with 2s delay between calls (rate limit safety)

**Current settings:**
- `MAX_GRANTS_PER_RUN = 25` (needs reducing to 10)
- `MIN_SCORE_THRESHOLD = 0.4` (needs raising to 0.6)
- `INTER_REQUEST_DELAY = 2` seconds

**Token usage:** ~100k tokens per run (4k per grant × 25 grants) — maxes out Groq's free daily limit in one execution.

### LOI Generator (`backend/services/writer.py`)
Groq generates a **7-section professional LOI:**
1. Organization Introduction
2. The Need (problem statement)
3. The Fit (why this grant matches)
4. The Impact (expected outcomes)
5. Budget Overview
6. Closing
7. Signature Block

Returns raw markdown prose, saved to `grant_matches.generated_loi`.

---

## 🗂️ Project Structure

```
grantmatch-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS
│   │   ├── database.py          # SQLAlchemy async session
│   │   ├── models/              # SQLAlchemy models
│   │   └── routers/             # API endpoints
│   ├── services/
│   │   ├── matcher.py           # AI matching engine
│   │   └── writer.py            # LOI generator
│   ├── scraper/
│   │   └── scrapers/
│   │       ├── grants_gov.py    # Grants.gov scraper (httpx)
│   │       └── foundation_scraper.py  # RWJF scraper (Playwright)
│   ├── alembic/                 # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # Route components
│   │   ├── components/          # Reusable UI components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utilities (supabase, axios)
│   │   └── App.jsx              # Router setup
│   ├── tailwind.config.js
│   └── package.json
└── README.md
```

---

## 🔧 Environment Variables

### Backend (`.env`)
```bash
DATABASE_URL=postgresql+asyncpg://postgres.xxx:[password]@host.pooler.supabase.com:6543/postgres?ssl=require
GROQ_API_KEY=gsk_your_key_here
FRONTEND_URL=https://grantmatchai.vercel.app
```

### Frontend (`.env`)
```bash
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=https://grantmatchai.onrender.com
```

---

## 🚧 Known Issues & Roadmap

### Critical Fixes Needed
- [ ] Reduce `MAX_GRANTS_PER_RUN` to 10 (token limit management)
- [ ] Add keyword pre-filter before Groq scoring (reduce API calls)
- [ ] Raise match threshold to 0.6 (improve match quality)
- [ ] Backend cold start warning in UI (Render free tier spins down)
- [ ] Remove "Gemini-Powered" badge (using Groq now)
- [ ] Progress indicator during matching ("Analyzing grant 3 of 10...")

### Nice to Have
- [ ] Landing page for public visitors
- [ ] Edit org details from navbar
- [ ] Send past funders to Groq for better matching context
- [ ] Empty state explains WHY no matches found
- [ ] Google OAuth (in addition to email/password)
- [ ] More grant sources beyond Grants.gov
- [ ] Match count badge on navbar

---

## 🎬 The Journey: How This Got Built

### **Day 1: Database Hell (The Foundation)**

Started with what should've been simple: set up PostgreSQL with SQLAlchemy. Spent **hours** debugging the Supabase connection string. Every variation failed:

- `sslmode=require` → Wrong (asyncpg doesn't use that syntax)
- Direct database URL → IPv6-only hostname, connection refused
- Typo in the Supabase project ID → 30 minutes wasted
- Finally: pooler URL with `ssl=require` + `statement_cache_size=0` worked

That last one? The `statement_cache_size=0` fix. pgbouncer prepared statement errors. Found it buried in a GitHub issue at what felt like 2 AM. The relief when `alembic upgrade head` finally succeeded was unreal.

Built all the SQLAlchemy models (Organizations, Grants, Matches), set up Alembic migrations, got basic CRUD working in FastAPI. Foundation laid. Exhausted.

---

### **Day 2: Scraping Success, Then Python 3.14 Betrayal**

**Morning:** Built the Grants.gov scraper using `httpx`. Hit their API, parsed `data["data"]["oppHits"]`, cleaned the data. **127 grants scraped successfully.** Felt like a win.

**Afternoon:** Tried to build a Playwright scraper for RWJF Foundation. Installed Playwright, wrote the `RWJFScraper` class, ran it.

```
ERROR: Playwright does not support Python 3.14
```

Searched for solutions. Found none. Python 3.14 came out **too recently** for Playwright to support it. Options:
1. Downgrade Python (breaks other dependencies)
2. Use Selenium (overkill)
3. Ship fallback data and move on

Chose #3. Hardcoded 3 RWJF grants manually. Moved on. Learned: bleeding edge has trade-offs.

---

### **Day 3: The AI Provider Graveyard**

**The Plan:** Use Claude (Anthropic API) for matching and LOI generation.

**8:00 AM:** Wrote the matching engine. Sent first request to Anthropic.

```
Error: Insufficient credits
```

Account out of credits. No time to add a payment method and wait for approval.

**9:30 AM:** Pivoted to Gemini. Rewrote prompts for Gemini's format. Tested. Worked beautifully. Ran the full matcher.

**11:45 AM:** Generated ~40 matches. Started LOI generation. Then:

```
Error 429: Quota exceeded
```

Gemini's free tier quota: **exhausted**. Mid-build. Half my matches had no LOIs.

**1:00 PM:** Discovered Groq. Free tier. Fast. `llama-3.3-70b-versatile` model. Rewrote everything **again** for Groq's API.

**2:30 PM:** First successful match run. Score: 0.87, reasoning: detailed and accurate. LOI generated: **genuinely impressive**. Seven professional sections. Funder-specific language. Better than I expected.

Groq became the hero. Anthropic and Gemini: the graveyard.

---

### **Day 4: React From Scratch**

Built the entire frontend in one day. Design system first (Button, Card, Badge, Spinner components), then pages:

- `/auth` — Sign in/sign up toggle
- `/onboarding` — Org profile form with focus area toggles
- `/dashboard` — AI matching trigger, org details
- `/grants` — Match cards with score bars, reasoning, deadline urgency
- `/loi/:id` — LOI viewer with copy-to-clipboard

**Tailwind v4 disaster:** Installed Tailwind, got v4 by default. Breaking changes everywhere. Config format changed. Build errors. Docs unhelpful. **Forced rollback to v3.** Lost an hour.

Built the `GrantCard` component: match score as a progress bar (green for high, yellow for medium, red for low), expandable reasoning section, deadline urgency badge ("Due in 3 days" → orange, "Urgent" → red). Looked clean.

React Query setup for data fetching. Auth context for Supabase. Axios interceptor for JWT tokens. All pages wired up. **Exhausted but functional.**

---

### **Day 5: Auth, Deployment, and the 2:45 AM Push**

**Morning:** Supabase auth integration. Sign up, sign in, JWT tokens. Protected routes with `ProtectedRoute` wrapper. FastAPI backend decoding JWTs with PyJWT.

**The Bug:** Users creating orgs → `user_id` was `null`. Why? `useEffect` for extracting `userId` from Supabase session didn't resolve before form submission. Race condition.

**Fix:** Added `userId` state, loading spinner until resolved, disabled submit button until ready. Manual SQL fix for existing orgs:

```sql
UPDATE organizations SET user_id = 'actual-uuid' WHERE user_id IS NULL;
```

**Evening: Deployment begins.**

- Backend to Render: Easy. Connected GitHub, set env vars, deployed. Worked first try.
- Frontend to Vercel: Easy. Connected GitHub, set env vars, deployed. Worked first try.

**11:30 PM:** Full flow test. Sign up → Create org → Trigger matching. Backend spun down (cold start). **53-second delay.** Finally responded. Matching ran.

**The Token Limit Panic:**

Matching finished. Checked Groq dashboard:

```
Daily token limit: 100,000
Tokens used: 98,247
```

One matching run consumed **the entire daily quota.** Math: 25 grants × ~4,000 tokens per grant = 100k. Realized the matcher is **way** too aggressive.

**Fix needed:** Reduce `MAX_GRANTS_PER_RUN` to 10, add keyword pre-filter before scoring. Didn't have time to deploy the fix that night.

**12:45 AM:** The LOI Caching Bug

Generated an LOI. Navigated to `/loi/:id`. Page showed "LOI not generated yet." But it **was** generated — I saw it in the database.

**Root cause:** React Query's `staleTime` default (5 minutes) served cached data from before the LOI was generated.

**Fix:** Added polling:

```javascript
refetchInterval: (data) => 
  data?.generated_loi ? false : 2000
```

Polls every 2 seconds until `generated_loi` is populated. Worked perfectly.

**2:45 AM:** Final test run. Sign up → Onboard → Match → Draft LOI → Copy to clipboard. **Everything worked.** Pushed to `main`. Auto-deployed to production.

Went to bed.

---

### **Day 6: The Polish (9:00 PM Success)**

**Afternoon:** Supabase email rate limit hit during testing. Free tier: **2 emails/hour**. Email confirmation was blocking signups.

**Fix:** Disabled "Confirm email" in Supabase Auth settings. Immediate signups now work.

Added toast notifications (`useToast` hook), error boundary for React crashes, empty states, deadline urgency logic, spinner animations.

**9:00 PM:** Full production test on live URLs. Sign up → Onboard → Match (waited through Render cold start) → Got 8 matches → Clicked "Draft LOI" → **Perfect LOI generated in 4 seconds** → Copied to clipboard.

**It worked. The whole damn thing worked.**

---

## 💀 The Graveyard: What Didn't Make It

- **Playwright scraper:** Python 3.14 incompatibility. RIP.
- **Anthropic API:** Insufficient credits. Gone.
- **Gemini:** Quota exhausted mid-build. Abandoned.
- **Tailwind v4:** Breaking changes. Rolled back to v3.
- **"Confirm email" flow:** Supabase rate limits. Disabled.
- **Sleep schedule:** Casualties of war.

---

## 🙏 Lessons Learned

1. **Read the connection string docs 10 times.** That pgbouncer fix saved me.
2. **Have a backup AI provider.** Went through 3 before landing on Groq.
3. **Test token limits BEFORE deploying.** Groq's daily quota is generous until you blow through it in one run.
4. **React Query's caching is smart but can bite you.** Polling solved the LOI bug.
5. **Cold starts are real.** Render free tier spins down. Warn users or upgrade.
6. **Bleeding edge = bleeding.** Python 3.14 + Playwright = incompatible.
7. **2 AM deploys work.** But test them at 9 PM the next day to be sure.

---

## 📜 License

MIT License — Use this, learn from it, build on it.

---

**Built with caffeine, Groq, and sheer determination.**  
**For nonprofits that deserve better tools.**

🌐 **Live:** [https://grantmatchai.vercel.app](https://grantmatchai.vercel.app)  
📦 **Repo:** [https://github.com/Mheet/grantmatch-ai](https://github.com/Mheet/grantmatch-ai)
