# CodePulse AI

> **Production-grade AI-powered Coding Activity Monitoring & Analytics Platform for colleges.**
> Supports 10,000+ users with real-time LeetCode/GitHub sync, Gemini AI analysis, and role-based dashboards.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, ShadCN UI, Recharts |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL (Neon) |
| Auth | JWT + RBAC |
| Task Queue | Celery + Redis |
| AI | Google Gemini 1.5 Flash |
| PDF | WeasyPrint + Jinja2 |
| Excel | openpyxl |
| Deploy: Frontend | Vercel |
| Deploy: Backend | Render |
| Deploy: DB | Neon PostgreSQL |
| CI/CD | GitHub Actions |
| Containers | Docker + Docker Compose |

---

## Quick Start (Local Development)

### Prerequisites
- Docker Desktop installed
- Python 3.11+
- Node.js 20+
- PostgreSQL (or Neon account)

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/codepulse-ai.git
cd codepulse-ai

# Backend environment
cp backend/.env.example backend/.env
# Edit backend/.env with your actual values

# Frontend environment
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with your API URL
```

### 2. Run with Docker Compose

```bash
# Start all services (backend, worker, beat, redis, nginx)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed initial data (roles, departments, admin user)
docker-compose exec backend python -m app.seeds.initial_seed
```

### 3. Run Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. Run Backend (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start FastAPI
uvicorn app.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A app.tasks.celery_app.celery_app worker --loglevel=info

# Start Celery beat (separate terminal)
celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) | ✅ |
| `JWT_SECRET_KEY` | Secret key for JWT (min 32 chars) | ✅ |
| `REDIS_URL` | Redis connection URL | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `GITHUB_TOKEN` | GitHub Personal Access Token | ✅ |
| `FRONTEND_URL` | Frontend URL for CORS | ✅ |
| `SMTP_HOST/USER/PASSWORD` | Email config for alerts | Optional |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_APP_NAME` | App name displayed in UI |

---

## User Roles

| Role | Description |
|---|---|
| **Student** | View personal LeetCode/GitHub stats, achievements, download reports |
| **Staff** | View personal stats + assigned mentees, add notes |
| **Admin** | Full system: user management, leaderboards, reports, AI analysis |

### Default Admin Account
After running seeds:
- Email: `admin@vsb.ac.in`
- Password: `Admin@12345` *(change immediately)*

---

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply all migrations
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history
```

---

## Running Tests

### Backend
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
# Coverage report: htmlcov/index.html
```

### Frontend
```bash
cd frontend
npm run test        # Vitest unit tests
npm run test:e2e    # Playwright E2E tests
```

---

## Deployment

### Vercel (Frontend)
```bash
cd frontend
npx vercel --prod
```

### Render (Backend)
1. Connect GitHub repo to Render
2. Set root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all env variables in Render dashboard

### Neon PostgreSQL
1. Create project at [neon.tech](https://neon.tech)
2. Copy connection string (use asyncpg driver)
3. Run migrations: `alembic upgrade head`

---

## Architecture

```
Users
  ↓ HTTPS
Vercel (Next.js 15)
  ↓ REST API
Render (FastAPI + Uvicorn)
  ↓
Neon PostgreSQL          Upstash Redis
  ↑
Celery Workers (Render background)
  ↓
LeetCode GraphQL API    GitHub REST API    Gemini API
```

---

## Features

- 🏆 **LeetCode Integration** — Stats, heatmap, contest rating, streak tracking
- 🐙 **GitHub Integration** — Commits, PRs, contribution graph, language breakdown
- 🤖 **Gemini AI Analysis** — Personalized recommendations, placement readiness
- 📊 **Role Dashboards** — Student, Staff, Admin with role-specific analytics
- 🥇 **Leaderboards** — Student, Staff, Department rankings
- 🏅 **Achievement System** — 10 badges with unlock conditions
- 📄 **PDF Reports** — Per-user professional PDF with WeasyPrint
- 📊 **Excel Exports** — Admin bulk export with 6 data sheets
- 🔔 **Alert System** — Inactivity, streak breaks, low performance alerts
- 📱 **Responsive** — Works on 375px mobile viewport
- 🌙 **Dark Mode** — Full dark/light mode with persistence
- 🔒 **Security** — bcrypt, JWT, RBAC, rate limiting, input validation

---

## License

MIT License — VSB Engineering College, 2025
