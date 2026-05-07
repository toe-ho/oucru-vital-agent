# 13 — Tech Stack

[← Back to Index](../00-index.md)

---

## Overview

This document details the technology choices for each layer of the system, with explicit justifications, trade-off notes, and compatibility considerations. The stack is optimized for: (1) Python-native biomedical signal processing via `vital_sqi`, `vitalDSP`, NumPy, SciPy, NeuroKit2, WFDB, Pandas, and PyArrow, (2) agentic AI orchestration using `smolagents` with local Ollama + Qwen3-8B, and (3) a clinical-grade web dashboard deployable on GCP within a student project budget.

---

## Full Stack Decision Table

| Layer | Technology | Version | Justification |
|---|---|---|---|
| **Frontend Framework** | Next.js + React + TypeScript | Next.js latest, React 18+, TS 5.x | Builds upload pages, dashboard screens, report viewer, and chatbot UI quickly with reusable components. Next.js provides routing, API-friendly project structure, and production-ready deployment defaults while still allowing client-side data fetching from FastAPI. |
| **UI Styling** | Tailwind CSS | Tailwind 3.x | Utility-first styling for fast dashboard layout, responsive views, and consistent component styling. |
| **Charting / Visualization** | Recharts | Recharts latest | Shows SQI trends, HR/HRV metrics, quality distribution, and window-level results with React-native chart components that are simple to customize and integrate with dashboard state. |
| **State Management** | TanStack Query (React Query) | v5 | Server state management with automatic background refetching, caching, and loading/error states. Eliminates boilerplate for API calls. Sufficient for this app — no need for Redux or Zustand. |
| **HTTP Client** | Axios | 1.x | Consistent request/response interceptors for auth headers and error normalization. Works well with TanStack Query. |
| **Backend Framework** | FastAPI (Python 3.11) | 0.111+ | Async-first, type-annotated endpoints with automatic OpenAPI/Swagger UI generation. Python-native — same runtime as OUCRU signal libraries and smolagents, no FFI boundary. Performance comparable to Node.js for I/O-bound workloads. |
| **Agent Framework** | smolagents | latest | Lets the LLM select approved Python tools for workflow planning, quality explanation, report drafting, and Q&A while keeping execution limited to registered tools. |
| **LLM Runtime** | Ollama + Qwen3-8B | Ollama latest, Qwen3-8B | Supports local-first workflow planning, report explanation, and chatbot Q&A without depending on external LLM APIs. |
| **Workflow Config** | YAML task plans + `config.yaml` | — | Stores task steps, thresholds, model settings, and workflow rules without hard-coding analysis behavior. |
| **Signal Processing** | vitalDSP + NumPy + SciPy | latest compatible | Handles filtering, peak detection, HR/HRV, SpO2 estimation, and numerical processing. |
| **Signal Quality** | vital-sqi / vitalSQI-toolkit | 0.1.2 | Provides SQI scoring and quality labels for ECG/PPG segments. |
| **ECG/PPG File & Feature Support** | NeuroKit2 + WFDB + Pandas + PyArrow | latest compatible | Supports ECG/PPG processing and common file formats, including CSV, Parquet, and WFDB records. |
| **Report Generation** | JSON + HTML/PDF export | — | Produces structured JSON reports and readable HTML/PDF QC reports for review and documentation. |
| **Database** | PostgreSQL | 15+ | Battle-tested relational database. JSONB columns for flexible SQI result storage and agent log parameters. Full ACID compliance for recording state transitions. Cloud SQL on GCP is managed and auto-backed-up. |
| **ORM + Migrations** | SQLAlchemy 2.0 + Alembic | SQLAlchemy 2.0, Alembic 1.13+ | Standard Python ORM with async support (`asyncpg` driver). Alembic for version-controlled schema migrations. Type-annotated models with `DeclarativeBase`. |
| **Async DB Driver** | asyncpg | 0.29+ | High-performance native asyncio PostgreSQL driver. Required for SQLAlchemy async sessions in FastAPI. |
| **Chatbot API** | FastAPI `POST /api/chat` (core endpoint) | — | Routes natural-language questions to the smolagents agent, which uses persisted SQI results, windowed quality values, threshold flags, and agent logs to return plain-language explanations. Multi-turn conversations are supported via `conversation_id`. Chat messages are persisted to the `chat_messages` table. |
| **Authentication** | Google OAuth/JWT + role-based access | — | Controls access for admin, researcher, reviewer, and read-only users. JWTs protect API calls after Google OAuth login, and RBAC limits privileged actions such as threshold updates and user management. |
| **Caching** | Redis (optional) | 7.x | Cache expensive dashboard aggregate queries and agent intermediate state. Optional for MVP — introduce if query latency becomes an issue. |
| **File Storage** | Local filesystem (dev) + GCS (prod) | Google Cloud Storage | Local storage simplifies development. Production uses a GCS bucket with signed URLs for file downloads. Abstracted behind a `StorageService` interface so the swap is a config change only. |
| **Task Queue** | FastAPI BackgroundTasks (MVP) → Celery + Redis (if needed) | — | For MVP, `BackgroundTasks` handles async signal processing without additional infrastructure. Celery introduced only if job queue management, retries, or worker scaling become necessary. |
| **Containerization** | Docker + Docker Compose | Docker 25+, Compose v2 | Single `docker compose up` starts all required services: Next.js frontend, FastAPI backend with OUCRU signal dependencies, PostgreSQL, and Ollama. Consistent environment across developer machines and CI. |
| **Cloud Platform** | Google Cloud Platform | — | OUCRU has existing GCP credits ($2–3K, expires Aug 23 2026). Cloud Run for stateless services, Cloud SQL for managed PostgreSQL, and GCS for file storage. Ollama/Qwen3-8B can run locally for development and on project-controlled compute for deployment demos. |
| **CI/CD** | GitHub Actions | — | Free for public/student repositories. Workflows: lint → test → build Docker image → push to Artifact Registry → deploy to Cloud Run. |
| **Backend Testing** | Pytest + pytest-asyncio + httpx | pytest 8.x | Standard Python testing. `httpx.AsyncClient` for FastAPI endpoint integration tests. `pytest-asyncio` for async test functions. |
| **Frontend Testing** | Jest/Vitest + React Testing Library | latest compatible | Component behavior testing for the Next.js/React frontend. |
| **API Documentation** | Swagger UI (FastAPI built-in) | — | Zero-configuration OpenAPI docs at `/docs`. Always synchronized with actual endpoint definitions. Interactive — allows manual API testing during development. |
| **Linting/Formatting** | Ruff (Python) + ESLint + Prettier (TS) | Ruff 0.4+, ESLint 9+ | Ruff replaces flake8 + isort + black for Python — single fast tool. ESLint + Prettier for TypeScript. Pre-commit hooks enforce both. |
| **Environment Config** | python-dotenv + Pydantic Settings + `config.yaml` | — | Backend reads deployment settings from `.env` via Pydantic `BaseSettings`; workflow steps, thresholds, and Ollama model settings live in YAML task plans and `config.yaml`. Frontend uses Next.js environment variables. |
| **PDF Generation** | WeasyPrint | weasyprint 60.x | HTML-to-PDF renderer. Reports are generated as HTML first, then converted to PDF. Simple integration — just `weasyprint.HTML(string=html).write_pdf(target)`. |
| **Progress Updates** | Polling via FastAPI status endpoints | — | MVP uses polling for assessment progress and completed-result refresh. Live waveform streaming and SSE/WebSocket progress are post-MVP/future scope. |

---

## Python Version Compatibility

The backend uses Python 3.11 for `vital_sqi`, `vitalDSP`, NumPy, SciPy, NeuroKit2, WFDB, Pandas, and PyArrow. These libraries run directly in the FastAPI backend container — no separate signal-processing microservice or version isolation is needed.

| Step | Action |
|---|---|
| **Runtime** | Backend (Python 3.11) installs OUCRU signal dependencies directly alongside FastAPI and smolagents. |
| **Dependency pinning** | Pin all versions in `backend/requirements.txt`. Use `pip-compile` (pip-tools) for a conflict-free lock file. |
| **Compatibility testing** | Run OUCRU signal-tool smoke tests in the Python 3.11 backend container in CI on first setup. |

---

### Signal Processing Dependency Chain

Install the OUCRU signal-processing dependencies in the backend container:

| Package | Purpose |
|---------|---------|
| vitalSQI-toolkit / vital-sqi | Signal quality index scoring and quality labels |
| vitalDSP | Digital signal processing, filtering, and peak detection |
| NumPy | Numeric array operations |
| SciPy | Scientific signal processing utilities |
| NeuroKit2 | ECG/PPG feature extraction support |
| WFDB | WFDB record support |
| Pandas | CSV/tabular signal data handling |
| PyArrow | Parquet file support |

These are included in `backend/requirements.txt`.

---

### CORS Configuration

FastAPI backend uses `CORSMiddleware`:
- Development: `allow_origins=["http://localhost:3000"]`
- Production: configured via `CORS_ORIGINS` environment variable
- Allows: GET, POST, PUT, DELETE methods; Authorization and Content-Type headers

---

## Budget Analysis

### Assumptions

- Project duration: **16 weeks** (4 months) (team-proposed timeline — to be confirmed with university supervisor)
- Development: primarily local Docker Compose (no cloud cost)
- Cloud resources provisioned from **Week 8** for staging and demo environments
- GCP credits available from OUCRU (estimated $2,000–$3,000 in existing credits; credits expire August 23, 2026)

### Monthly GCP Cost Estimates

| Resource | Spec | Est. Monthly Cost |
|---|---|---|
| **Ollama runtime** | Qwen3-8B on local machine or project-controlled compute | Depends on host; no per-token API cost |
| **Cloud Run** (FastAPI backend) | 1 vCPU, 512 MB RAM, ~1000 req/day | ~$5–10 |
| **Cloud Run** (Next.js frontend) | Small container, minimal traffic | ~$2–5 |
| **Cloud SQL** (PostgreSQL 15) | `db-f1-micro`, 10 GB SSD, single zone | ~$15–20 |
| **Google Cloud Storage** | 50 GB standard storage, minimal egress | ~$1–2 |
| **Artifact Registry** | Docker image storage, ~5 GB | ~$0.50 |
| **Networking / Egress** | Minimal for internal project traffic | ~$2–5 |
| **Total (monthly)** | | **~$30–65 / month** |

> **Savings note:** Local-first Ollama usage avoids per-token API charges during development. If Qwen3-8B is hosted for demos, the main cost variable is the chosen compute host rather than LLM API usage.

### Total Project Cost (16 weeks ≈ 4 months)

| Scenario | Cost |
|---|---|
| Conservative (T4 preemptible, minimal uptime) | ~$460–700 |
| Moderate (staging always on, demos) | ~$600–900 |
| **Within $2–3K budget** | Yes — significant headroom |

### Cost Optimization Notes

- **Ollama + Qwen3-8B**: no per-token API costs during local development.
- **Scale to zero** on Cloud Run during off-hours where service behavior allows.
- Shut down Cloud SQL when not actively needed during development weeks.
- Keep Qwen3-8B model settings in `config.yaml` so local and deployment environments are reproducible.

---

## Architecture Diagram (Text)

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                         │
│           Next.js + React + TypeScript + Tailwind CSS             │
│           Recharts dashboards │ API client layer                  │
└───────────────────────┬──────────────────────────────────────────┘
                        │ HTTPS / REST + SSE (progress updates)
┌───────────────────────▼──────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11)                  │
│   Endpoints │ BackgroundTasks │ SQLAlchemy 2.0 async │ asyncpg   │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              smolagents Agent Orchestrator               │   │
│   │  Tool registry │ YAML task plans │ Ollama client        │   │
│   │  Chatbot handler (POST /api/chat)                        │   │
│   └──────────────────────┬──────────────────────────────────┘   │
│                           │ direct Python imports                │
│   ┌───────────────────────▼──────────────────────┐              │
│   │        OUCRU signal tools (Python 3.11)       │              │
│   │  load_signal_file() │ compute_sqi()            │              │
│   │  compute_sqi_windowed() │ preprocess_ppg()    │              │
│   │  HRV, SpO2, DC-layer, threshold helpers       │              │
│   └───────────────────────┬──────────────────────┘              │
│                           │                                      │
│   ┌───────────────────────▼──────────────────────┐              │
│   │         Local Ollama LLM Runtime              │              │
│   │  Qwen3-8B for workflow/report/Q&A reasoning  │              │
│   └───────────────────────┬──────────────────────┘              │
│                           │ Ollama + Qwen3-8B                    │
└───────────┬───────────────┼──────────────────────┬──────────────┘
            │               │                      │
  ┌─────────▼──────────┐    │             ┌────────▼────────────────┐
  │   PostgreSQL 15     │    │             │  Ollama Runtime         │
  │   Cloud SQL (prod)  │    │             │  → Qwen3-8B             │
  │   recordings        │    │             │  workflow/report/Q&A    │
  │   segments          │    │             └─────────────────────────┘
  │   sqi_results       │
  │   reports           │
  │   agent_logs        │
  │   settings          │    ┌─────────────────────────┐
  └────────────────────┘    │  GCS / Local Filesystem  │
                             │  Signal file storage     │
                             └─────────────────────────┘
```

---

## Local Development Quickstart

```bash
# 1. Clone and configure
git clone <repo-url> && cd vital-agent
cp .env.example .env
# Configure Ollama/Qwen3-8B settings in config.yaml

# 2. Start all required services
docker compose up -d

# 3. Run database migrations
docker exec backend alembic upgrade head

# 4. Seed default settings
docker exec backend python -m app.scripts.seed_settings

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs (Swagger UI)
# Ollama (if profile enabled): http://localhost:11434 (internal)
```

A `Makefile` provides shortcuts: `make up`, `make down`, `make migrate`, `make seed`, `make logs`.
