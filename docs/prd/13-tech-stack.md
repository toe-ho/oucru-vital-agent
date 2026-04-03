# 13 — Tech Stack

[← Back to Index](00-index.md)

---

## Overview

This document details the technology choices for each layer of the system, with explicit justifications, trade-off notes, and compatibility considerations. The stack is optimized for: (1) Python-native biomedical signal processing via `vital_sqi`, (2) agentic AI orchestration using Google Gemini 2.0 Flash via Vertex AI as the primary LLM (with Ollama self-hosted as optional fallback), and (3) a clinical-grade web dashboard deployable on GCP within a student project budget.

---

## Full Stack Decision Table

| Layer | Technology | Version | Justification |
|---|---|---|---|
| **Frontend Framework** | React + TypeScript (Vite) | React 18, TS 5.x, Vite 5.x | Modern, type-safe, fast HMR dev server. Vite chosen over Next.js because SSR is not needed — all data is fetched client-side from the FastAPI backend. Simpler deployment as a static bundle on Cloud Run or GCS. **Team consideration:** For a beginner team, alternatives like Streamlit or Gradio were considered but React/TypeScript was chosen for its long-term maintainability, industry relevance, and richer dashboard capabilities. The team should allocate extra time in Phase 3 for frontend learning curve. |
| **UI Component Library** | shadcn/ui + Tailwind CSS | shadcn/ui latest, Tailwind 3.x | Unstyled Radix UI primitives with Tailwind utilities. Clean, accessible components ideal for data-dense dashboards. Fully customizable — no opaque CSS overrides needed. Excellent DX with copy-paste component model. |
| **Charting / Visualization** | Plotly.js (`react-plotly.js`) | Plotly.js 2.x | Supports multi-channel biomedical waveform display natively. Interactive zoom, pan, and range selection without additional plugins. Used internally by `vital_sqi` for its own plots — ensures visual consistency. WebGL renderer (`scattergl`) handles long signal arrays (>100k points) without frame drops. |
| **State Management** | TanStack Query (React Query) | v5 | Server state management with automatic background refetching, caching, and loading/error states. Eliminates boilerplate for API calls. Sufficient for this app — no need for Redux or Zustand. |
| **HTTP Client** | Axios | 1.x | Consistent request/response interceptors for auth headers and error normalization. Works well with TanStack Query. |
| **Backend Framework** | FastAPI (Python 3.11) | 0.111+ | Async-first, type-annotated endpoints with automatic OpenAPI/Swagger UI generation. Python-native — same runtime as `vital_sqi` and LangGraph, no FFI boundary. Performance comparable to Node.js for I/O-bound workloads. |
| **Agent Framework** | LangGraph | 0.2.x | Stateful, graph-based multi-step agent orchestration. Explicit node/edge definition gives full control over agent flow — better than LangChain's chain abstraction for a sequential analysis pipeline. Built-in support for tool-calling, conditional branching, and state persistence. |
| **LLM (Primary)** | Google Gemini 2.0 Flash (Vertex AI) | latest | Covered by GCP credits. Excellent tool-calling and native function calling support. No GPU infrastructure needed. LangGraph integration via `langchain-google-vertexai`. |
| **LLM (Fallback)** | Ollama + Llama 3.1 8B | Ollama 0.3.x | Optional self-hosted fallback for offline/demo use. Activated via Docker Compose profile (`--profile local-llm`). |
| **LLM Serving** | Vertex AI API (primary) / Ollama (fallback) | — | Primary: API call to Vertex AI, no serving infrastructure required. Fallback: Ollama Docker container started with `docker compose --profile local-llm up`. Switch via `LLM_PROVIDER=gemini\|ollama` env var. |
| **Database** | PostgreSQL | 15+ | Battle-tested relational database. JSONB columns for flexible SQI result storage and agent log parameters. Full ACID compliance for recording state transitions. Cloud SQL on GCP is managed and auto-backed-up. |
| **ORM + Migrations** | SQLAlchemy 2.0 + Alembic | SQLAlchemy 2.0, Alembic 1.13+ | Standard Python ORM with async support (`asyncpg` driver). Alembic for version-controlled schema migrations. Type-annotated models with `DeclarativeBase`. |
| **Async DB Driver** | asyncpg | 0.29+ | High-performance native asyncio PostgreSQL driver. Required for SQLAlchemy async sessions in FastAPI. |
| **Chatbot API** | FastAPI `POST /api/chat` (core endpoint) | — | Routes natural-language questions to the LangGraph agent, which calls `get_segment_detail` and returns plain-language explanations. Multi-turn conversations are supported via `conversation_id`. Chat messages are persisted to the `chat_messages` table. No additional library needed beyond the existing LangGraph + LLM stack. |
| **Token-Encoding Privacy Layer** | Custom Python module (`backend/app/agent/privacy_layer.py`) | — | Core component that encodes patient-identifiable tokens (subject ID, device ID, recording ID, file path) in every outgoing LLM prompt and decodes them from every LLM response. Implemented as a stateless per-request utility wrapping all `llm.invoke()` / `llm.astream()` calls inside the agent nodes. Zero external dependencies — pure Python string replacement with a session-scoped mapping table. |
| **Caching** | Redis (optional) | 7.x | Cache expensive dashboard aggregate queries and agent intermediate state. Optional for MVP — introduce if query latency becomes an issue. |
| **File Storage** | Local filesystem (dev) + GCS (prod) | Google Cloud Storage | Local storage simplifies development. Production uses a GCS bucket with signed URLs for file downloads. Abstracted behind a `StorageService` interface so the swap is a config change only. |
| **Task Queue** | FastAPI BackgroundTasks (MVP) → Celery + Redis (if needed) | — | For MVP, `BackgroundTasks` handles async signal processing without additional infrastructure. Celery introduced only if job queue management, retries, or worker scaling become necessary. |
| **Containerization** | Docker + Docker Compose | Docker 25+, Compose v2 | Single `docker compose up` starts all required services: frontend dev server, FastAPI backend (with vital_sqi), PostgreSQL. Ollama activated via `--profile local-llm`. Consistent environment across developer machines and CI. |
| **Cloud Platform** | Google Cloud Platform | — | OUCRU has existing GCP credits ($2–3K, expires Aug 23 2026). Cloud Run for stateless services (frontend, backend). Cloud SQL for managed PostgreSQL. GCS for file storage. Gemini API via Vertex AI — no GPU infrastructure needed. |
| **CI/CD** | GitHub Actions | — | Free for public/student repositories. Workflows: lint → test → build Docker image → push to Artifact Registry → deploy to Cloud Run. |
| **Backend Testing** | pytest + pytest-asyncio + httpx | pytest 8.x | Standard Python testing. `httpx.AsyncClient` for FastAPI endpoint integration tests. `pytest-asyncio` for async test functions. |
| **Frontend Testing** | Vitest + React Testing Library | Vitest 1.x | Fast Vite-native test runner. RTL for component behavior testing. No Puppeteer/Playwright for MVP scope. |
| **API Documentation** | Swagger UI (FastAPI built-in) | — | Zero-configuration OpenAPI docs at `/docs`. Always synchronized with actual endpoint definitions. Interactive — allows manual API testing during development. |
| **Linting/Formatting** | Ruff (Python) + ESLint + Prettier (TS) | Ruff 0.4+, ESLint 9+ | Ruff replaces flake8 + isort + black for Python — single fast tool. ESLint + Prettier for TypeScript. Pre-commit hooks enforce both. |
| **Environment Config** | python-dotenv + Pydantic Settings | — | Backend reads from `.env` file via Pydantic `BaseSettings`. Type-validated config with defaults. Frontend uses Vite's `import.meta.env` with `.env.local`. |
| **PDF Generation** | WeasyPrint | weasyprint 60.x | HTML-to-PDF renderer. Reports are generated as HTML first, then converted to PDF. Simple integration — just `weasyprint.HTML(string=html).write_pdf(target)`. |
| **Real-time Updates** | SSE (Server-Sent Events) via FastAPI `StreamingResponse` | — | Used for assessment progress updates. Simpler than WebSocket, works through proxies. Frontend uses `EventSource` API. Polling as fallback for older browsers. |

---

## Python Version Compatibility

`vital_sqi` supports Python >=3.7 (tested on 3.7, 3.8, 3.9, 3.11). The backend uses Python 3.11, which is fully compatible. `vital_sqi` is installed directly via `pip install vitalSQI-toolkit` in the backend container — no separate microservice or version isolation is needed.

| Step | Action |
|---|---|
| **Runtime** | Backend (Python 3.11) installs `vitalSQI-toolkit` directly alongside FastAPI and LangGraph. |
| **Dependency pinning** | Pin all versions in `backend/requirements.txt`. Use `pip-compile` (pip-tools) for a conflict-free lock file. |
| **Compatibility testing** | Run `vital_sqi` smoke tests in the Python 3.11 backend container in CI on first setup. |

---

### vital_sqi Dependency Chain

Install `vitalSQI-toolkit` in the backend container. Actual dependencies from the package:

| Package | Version Constraint | Purpose |
|---------|-------------------|---------|
| vitalSQI-toolkit | 0.1.2 | Signal quality index computation |
| vitalDSP | (any) | Digital signal processing (required by vital_sqi) |
| numpy | >=1.20.2 | Array operations |
| pandas | >=1.1.5 | DataFrame handling |
| scipy | >=1.6.0 | Signal processing |
| scikit-learn | >=0.24.1 | ML utilities |
| plotly | >=4.14.3 | Visualization |
| pyEDFlib | >=0.1.20 | EDF file I/O |
| wfdb | >=3.3.0 | MIT file I/O |
| statsmodels | >=0.12.2 | Statistical models |
| pmdarima | >=1.8.0 | Time series analysis |
| pycwt | >=0.3.0a22 | Wavelet transforms |
| matplotlib | (any) | Plotting |
| openpyxl | (any) | Excel I/O |
| datetimerange | >=1.0.0 | Datetime handling |
| dateparser | >=1.0.0 | Date parsing |
| tqdm | >=4.56.0 | Progress bars |

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
| **Vertex AI API** (Gemini 2.0 Flash) | ~1,000–2,000 input tokens + ~500 output tokens per assessment; hundreds of assessments/month | ~$5–20 |
| **Cloud Run** (FastAPI backend) | 1 vCPU, 512 MB RAM, ~1000 req/day | ~$5–10 |
| **Cloud Run** (Frontend static) | Nginx container, minimal traffic | ~$2–5 |
| **Cloud SQL** (PostgreSQL 15) | `db-f1-micro`, 10 GB SSD, single zone | ~$15–20 |
| **Google Cloud Storage** | 50 GB standard storage, minimal egress | ~$1–2 |
| **Artifact Registry** | Docker image storage, ~5 GB | ~$0.50 |
| **Networking / Egress** | Minimal for internal project traffic | ~$2–5 |
| **Total (monthly)** | | **~$30–65 / month** |

> **Savings note:** Switching from a self-hosted T4 GPU VM (~$90–130/month) to Gemini API (~$5–20/month) reduces monthly cloud cost by ~60%, freeing budget for compute and storage. No dedicated GPU VM is required.

### Total Project Cost (16 weeks ≈ 4 months)

| Scenario | Cost |
|---|---|
| Conservative (T4 preemptible, minimal uptime) | ~$460–700 |
| Moderate (staging always on, demos) | ~$600–900 |
| **Within $2–3K budget** | Yes — significant headroom |

### Cost Optimization Notes

- **Gemini API** (primary): zero infrastructure overhead — no GPU VM to manage. Costs scale with actual usage, making it ideal for a capstone project with variable assessment volume.
- **Scale to zero** on Cloud Run during off-hours (default behavior).
- **Ollama fallback** (CPU-only) is available via `docker compose --profile local-llm up` if Gemini API is unavailable or GCP credits run low — Llama 3.1 8B at 4-bit runs at ~2–3 tokens/second on CPU, acceptable for demos and offline development.
- Shut down Cloud SQL when not actively needed during development weeks.
- Add `langchain-google-vertexai` to backend Python dependencies for Gemini/Vertex AI integration.

---

## Architecture Diagram (Text)

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                         │
│           React 18 + TypeScript + Vite + shadcn/ui               │
│           Plotly.js waveforms │ TanStack Query API layer         │
└───────────────────────┬──────────────────────────────────────────┘
                        │ HTTPS / REST + SSE (progress updates)
┌───────────────────────▼──────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11)                  │
│   Endpoints │ BackgroundTasks │ SQLAlchemy 2.0 async │ asyncpg   │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              LangGraph Agent Orchestrator                │   │
│   │  ReAct loop │ Tool registry │ State graph │ LLM client  │   │
│   │  Chatbot handler (POST /api/chat)                        │   │
│   └──────────────────────┬──────────────────────────────────┘   │
│                           │ direct Python imports                │
│   ┌───────────────────────▼──────────────────────┐              │
│   │         vital_sqi library (Python 3.11)       │              │
│   │  get_ecg_sqis() │ get_ppg_sqis()              │              │
│   │  get_qualified_ecg() │ get_qualified_ppg()    │              │
│   │  segment_split() │ preprocess functions       │              │
│   └───────────────────────┬──────────────────────┘              │
│                           │                                      │
│   ┌───────────────────────▼──────────────────────┐              │
│   │     Token-Encoding Privacy Layer              │              │
│   │  Encodes PII tokens → LLM; decodes ← LLM     │              │
│   └───────────────────────┬──────────────────────┘              │
│                           │ BaseLLMProvider (factory)            │
└───────────┬───────────────┼──────────────────────┬──────────────┘
            │               │                      │
  ┌─────────▼──────────┐    │             ┌────────▼────────────────┐
  │   PostgreSQL 15     │    │             │  GeminiProvider [default]│
  │   Cloud SQL (prod)  │    │             │  → Vertex AI API (GCP)  │
  │   recordings        │    │             ├─────────────────────────┤
  │   segments          │    │             │  OllamaProvider [opt.]  │
  │   sqi_results       │    │             │  → Ollama :11434        │
  │   reports           │    │             └─────────────────────────┘
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
# Set LLM_PROVIDER=gemini and GOOGLE_CLOUD_PROJECT=<your-project-id> in .env

# 2. Start all required services (Gemini API — no Ollama container needed)
docker compose up -d

# (Optional) To use Ollama instead of Gemini, start with the local-llm profile:
# LLM_PROVIDER=ollama docker compose --profile local-llm up -d

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
