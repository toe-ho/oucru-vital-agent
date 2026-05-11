# OUCRU Vital Agent

Agentic AI system for wearable physiological signal (ECG/PPG) data quality monitoring.
Built for Oxford University Clinical Research Unit (OUCRU).

Combines `vital-sqi` + `vitalDSP` signal processing with a local LLM (Qwen3 via Ollama)
to automate quality assessment of high-frequency wearable recordings.

---

## Architecture

```
Upload (EDF/CSV/Parquet)
        ↓
  FastAPI Backend
        ↓
  Agent Orchestrator  ←→  Ollama (Qwen3-8B, local)
        ↓
  8 Signal Tools
  ├── load_signal_file      (file I/O: CSV, Parquet, WFDB)
  ├── compute_sqi           (overall Signal Quality Index)
  ├── compute_sqi_windowed  (per-window SQI classification)
  ├── preprocess_ppg        (bandpass filter + peak detection)
  ├── extract_hrv_features  (time + frequency domain HRV)
  ├── estimate_spo2         (ratio-of-ratios SpO2)
  ├── extract_ppg_dc_layer  (hemodynamic baseline trend)
  └── check_clinical_thresholds (HR, SpO2, SQI flagging)
        ↓
  PostgreSQL  →  Report (PDF/HTML)  →  Next.js Frontend
```

---

## Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python 3.11 |
| Agent framework | smolagents CodeAgent |
| LLM | Qwen3-8B via Ollama (local, no API key) |
| Signal processing | vitalDSP + vital-sqi |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 async |
| Migrations | Alembic (async) |
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS |
| Charts | Recharts |
| Report generation | Jinja2 + WeasyPrint (PDF) |
| Container | Docker Compose |

---

## Quick start (Docker)

```bash
# 1. Copy env file and set your SECRET_KEY
cp .env.example .env

# 2. Start all services (frontend, backend, postgres, ollama)
make up

# 3. Run database migrations
make migrate

# 4. Seed default threshold settings
make seed

# 5. Open the app
open http://localhost:3000
```

The first startup pulls `qwen3:8b` (~5 GB) into the Ollama container automatically.

---

## Quick start (local dev, no Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Update config.yaml: set llm.base_url = http://localhost:11434
# Start Ollama locally: ollama serve && ollama pull qwen3:8b

DATABASE_URL=postgresql+asyncpg://oucru:oucru@localhost:5432/oucru \
SECRET_KEY=dev-secret \
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Project structure

```
vital-agent/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── core.py              # OllamaAgent raw loop + smolagents runner (CLI)
│   │   │   ├── orchestrator.py      # FastAPI background task pipeline
│   │   │   ├── fallback.py          # Rule-based fallback when LLM unavailable
│   │   │   ├── state.py             # AgentState TypedDict
│   │   │   ├── tool_registry.py     # ALL_TOOLS list for smolagents
│   │   │   ├── prompts/             # System prompt text
│   │   │   └── task_plans/          # YAML workflows (ppg_plan, ecg_plan, fluid_response)
│   │   ├── api/                     # FastAPI route handlers
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── services/                # Business logic (assessment, report, settings)
│   │   ├── tools/                   # 8 agent tools (signal_loader, sqi, ppg, hrv, spo2, ...)
│   │   ├── db/                      # Session factory + DB init
│   │   ├── templates/               # Jinja2 report template
│   │   ├── config.py                # Settings (pydantic-settings) + AgentConfig
│   │   └── main.py                  # FastAPI app factory
│   ├── alembic/                     # Database migrations
│   ├── scripts/                     # CLI runner + folder watcher
│   ├── tests/
│   │   ├── unit/                    # Tool unit tests (one file per tool)
│   │   ├── integration/             # API endpoint tests
│   │   └── performance/             # Throughput benchmarks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Upload page (Screen 1)
│   │   ├── dashboard/               # Quality dashboard (Screen 3)
│   │   ├── settings/                # Threshold settings (Screen 5)
│   │   └── recordings/[id]/
│   │       ├── monitor/             # Waveform monitor (Screen 2)
│   │       ├── report/              # Report viewer (Screen 4)
│   │       └── chat/                # Agent chatbot (Screen 6)
│   ├── components/
│   ├── services/                    # API client + per-domain service modules
│   ├── types/api.ts                 # TypeScript API interfaces
│   └── Dockerfile
├── dev_docs/                        # Architecture and design notes
├── config.yaml                      # Agent + signal config (mounted into backend)
├── docker-compose.yml
├── docker-compose.test.yml          # Isolated test environment
├── lighthouserc.yml                 # Frontend performance targets
├── Makefile
└── .env.example
```

---

## API overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a signal file |
| `GET` | `/api/recordings` | List recordings |
| `GET` | `/api/recordings/{id}` | Recording detail |
| `GET` | `/api/recordings/{id}/waveform` | Waveform data (downsampled) |
| `POST` | `/api/assess` | Trigger quality assessment |
| `GET` | `/api/assessment-jobs/{id}` | Job status |
| `GET` | `/api/assessment-jobs/{id}/results` | Segment results + summary |
| `GET` | `/api/assessment-jobs/{id}/logs` | Agent decision log |
| `POST` | `/api/reports/generate` | Generate PDF/HTML report |
| `GET` | `/api/reports/{id}` | Fetch report (JSON/HTML/PDF) |
| `GET` | `/api/dashboard/summary` | KPI summary |
| `POST` | `/api/chat` | One-shot agent chat |
| `GET/PUT` | `/api/settings/thresholds` | Read/update SQI thresholds |
| `GET` | `/api/health` | Health check |

Full OpenAPI docs available at `http://localhost:8000/docs` when running.

---

## Running tests

```bash
# All tests in Docker
make test

# Backend only, with HTML coverage report
make test-local
open backend/htmlcov/index.html

# Performance benchmarks (slow — run manually)
cd backend && pytest tests/performance/ -v -s
```

Coverage target: **80%** (enforced in CI).

---

## Configuration

`config.yaml` controls agent behavior and signal thresholds. Key fields:

| Key | Default | Description |
|---|---|---|
| `llm.model` | `qwen3:8b` | Ollama model name |
| `llm.base_url` | `http://ollama:11434` | Ollama URL (change to `localhost:11434` for local CLI) |
| `agent.max_steps` | `15` | Max LLM tool calls per assessment |
| `agent.timeout_seconds` | `300` | Fallback trigger timeout |
| `signal.default_window_sec` | `30` | SQI window duration |
| `thresholds.sqi_min` | `0.5` | Minimum acceptable SQI |

SQI thresholds are also runtime-configurable via the Settings page (persisted to DB).
