# OUCRU Vital Agent

Agentic waveform data quality monitoring for ECG and PPG signals. Accepts de-identified recordings, computes signal quality indices (SQI) via `vital_sqi`, classifies segments with a `smolagents` `ToolCallingAgent`, and exposes results through a practitioner dashboard and grounded chatbot.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.111+, Python 3.11 |
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| Agent | smolagents + Ollama + Qwen3-8B |
| Signal QA | vital_sqi, vitalDSP, NeuroKit2 |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 + Alembic |
| Storage | Local filesystem (dev) → GCS (prod) |
| Auth | Google OAuth / JWT, RBAC |

## Quick Start

### Prerequisites

- Docker 25+ and Compose v2
- Google OAuth client credentials

### 1. Configure Environment

```bash
# Root .env — ports and database credentials
cp .env.example .env
# Edit .env to change BACKEND_PORT, FRONTEND_PORT, POSTGRES_PORT if needed

# Backend .env — secrets only
cp backend/.env.example backend/.env
# Edit to set: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET_KEY

# Frontend .env.local — secrets only
cp frontend/.env.example frontend/.env.local
```

### 2. Start Services

```bash
# Without Ollama (deterministic fallback only)
docker compose up -d

# With Ollama (full LLM capabilities)
docker compose --profile ollama up -d
docker compose exec ollama ollama pull qwen3:8b
```

### 3. Initialize Database

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed
```

### Default Ports

- Frontend: http://localhost:3000
- Backend API + Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Ollama (if enabled): localhost:11434

## Local Development (Without Docker)

For rapid iteration without Docker:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/oucru_vital"
export GOOGLE_CLIENT_ID="..." GOOGLE_CLIENT_SECRET="..."
uvicorn app.main:app --reload

# Frontend (in separate terminal)
cd frontend
npm install
npm run dev  # http://localhost:3000
```

Requires local PostgreSQL running (or adjust DATABASE_URL).

## Makefile Shortcuts

```bash
make up        # docker compose up -d
make down      # docker compose down
make migrate   # alembic upgrade head
make seed      # seed roles and default settings
make test      # run backend + frontend tests
make lint      # ruff + eslint
make logs      # docker compose logs -f
```

## Testing

```bash
# Backend (pytest)
cd backend && pytest

# Frontend (Jest)
cd frontend && npm test

# Run all tests (via Make)
make test
```

## Data Privacy

- Accept only de-identified waveform files (ECG/PPG)
- Do not upload patient-identifiable data
- Raw waveform arrays must never appear in LLM prompts or logs; use `signal_ref` references
- Commit no secrets, credentials, or raw signal arrays

## Project Scope (MVP)

- CSV and Parquet file upload (single + batch ≤50 files)
- Single-channel assessment (ECG or PPG per file)
- Google OAuth/JWT authentication with role-based access control
- Signal quality classification with vital_sqi
- Agentic assessment interpretation with fallback
- Segment override feedback governance
- Practitioner dashboard and grounded chatbot
- Local Docker deployment

**Post-MVP:** EDF/WFDB support, multi-channel processing, cloud deployment, automated retraining.

## Documentation

- **`README.md`** — This file; project overview and quick start
- **`docs/project-overview-pdr.md`** — Product requirements, goals, user roles, MVP scope
- **`docs/codebase-summary.md`** — Full codebase structure and file organization
- **`docs/code-standards.md`** — Coding conventions, architecture patterns, error handling
- **`docs/system-architecture.md`** — Component interactions, data flow, database schema
- **`docs/development-roadmap.md`** — Phase status, milestones, acceptance criteria
- **`docs/project-changelog.md`** — Version history and feature tracking
- **`docs/design-guidelines.md`** — Frontend UI/UX standards, color tokens, components
- **`docs/deployment-guide.md`** — Docker setup, migrations, environment configuration
- **`CLAUDE.md`** — Development workflows and code standards
- **`docs/prd/`** — Full product requirements documentation

## Key Design Rules

1. **No raw waveform arrays in LLM context** — Use `SignalRef` and retrieve metadata only
2. **Immutable AI classification** — `segments.classification` is write-once; overrides are append-only events
3. **Report freshness tracking** — Reports marked stale when overrides postdate generation
4. **LLM graceful fallback** — Assessment completes with rule-based classification if Ollama unavailable
5. **Google OAuth required** — No unauthenticated product paths
6. **Audit trail** — All mutations logged with request IDs for compliance

## Contributing

1. Read `CLAUDE.md` for development workflows
2. Follow `docs/code-standards.md` for code style
3. Run `make lint` and `make test` before pushing
4. Keep code files under 200 lines when practical
5. Use kebab-case for filenames, snake_case for Python, conventions for TypeScript/React

## Support

For issues, questions, or contributions:
- **Documentation:** See `docs/` directory
- **Development:** See `CLAUDE.md` and GitHub
- **Planning:** See `plans/` for implementation details
- **Tests:** Run `make test` locally
