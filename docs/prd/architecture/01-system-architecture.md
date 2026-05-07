# 08 — System Architecture

[← Back to Index](../00-index.md)

---

**Scope:** This architecture addresses waveform data (ECG, PPG) only. Imaging data quality monitoring is deferred to future phases per project scope decisions.

---

## 1. High-Level Architecture Overview

The system is organized as a **monorepo** containing a Python backend and a TypeScript frontend. The frontend communicates with the backend via REST. Both services are independently containerized and orchestrated via Docker Compose.

**Design rationale:**
- OUCRU signal-processing dependencies run directly in the same backend container alongside FastAPI and smolagents. No separate microservice is needed.
- Next.js, React, TypeScript, and Tailwind CSS provide a modern, type-safe dashboard with strong ecosystem support.
- REST over HTTP keeps every contract simple, well-documented, and language-agnostic.
- Monorepo simplifies dependency management, shared configuration, and CI/CD pipelines.

---

## 2. Monorepo Structure

```
vital-agent/
├── backend/                  # Python 3.11 — FastAPI + smolagents + OUCRU signal tools
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── agent/            # smolagents orchestration logic
│   │   ├── tools/            # Approved Python tools for signal analysis
│   │   ├── services/         # Report generation, data processing
│   │   └── api/              # REST endpoint definitions
│   ├── requirements.txt      # Includes OUCRU signal dependencies
│   └── Dockerfile
├── frontend/                 # TypeScript — Next.js + React + Tailwind CSS
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── package.json
│   └── Dockerfile
├── docs/
├── docker-compose.yml
└── README.md
```

### Key directory notes

| Directory | Responsibility |
|-----------|---------------|
| `backend/app/agent/` | All smolagents orchestration logic, prompt templates, task-plan loading, and decision loops |
| `backend/app/tools/` | Approved Python tools for OUCRU signal analysis — standard Python imports, no HTTP overhead |
| `backend/app/services/` | Business logic decoupled from HTTP: report generation, file parsing, DB access |
| `backend/app/api/` | FastAPI routers; no business logic — delegates immediately to services or agent |
| `frontend/services/` | All HTTP calls to the backend; typed request/response interfaces |

---

## 3. Communication Pattern

```
Browser
  ↓  (HTTP/HTTPS)
Next.js + React Frontend  (port 3000)
  ↓  (HTTP REST API)
FastAPI Backend  (port 8000, Python 3.11)
  ├──→ OUCRU signal tools  (direct Python imports)
  ├──→ Ollama + Qwen3-8B  (port 11434)
  └──→ PostgreSQL  (port 5432)
```

The LLM runtime is local Ollama + Qwen3-8B. Input files are assumed to be de-identified before upload, and the agent must not send raw waveform arrays to the LLM; prompts should contain only metadata, tool outputs, SQI summaries, and report context needed for explanation.

- The browser communicates only with the frontend service (Next.js + React).
- The frontend calls the FastAPI backend via typed REST endpoints.
- FastAPI delegates assessment requests to the smolagents workflow.
- The backend imports OUCRU signal-processing libraries directly as Python packages — no inter-service HTTP calls needed.
- Results flow back up the chain and are persisted to PostgreSQL and file storage before being returned to the client.

---

## 4. Application Flow (10 Steps)

### Step 1 — Data Upload
The researcher uploads a waveform file (1–2 hour ECG or PPG recording) through the web dashboard. Supported formats: ECG — EDF, MIT/WFDB, CSV, Parquet; PPG — CSV, Parquet. The frontend sends a `POST /api/upload` multipart request carrying the file and metadata (signal type, sampling rate). The backend validates the file, stores it in object storage, and creates a `Recording` record in PostgreSQL with status `uploaded`.

### Step 2 — Agent Activation
The backend publishes a processing job (or directly calls the agent service). The agent is instantiated and receives a context object containing the recording ID, file path, signal type, and sampling rate. The smolagents workflow uses Ollama + Qwen3-8B to reason about which approved OUCRU tool sequence to invoke: load the waveform with `load_signal_file`, compute quality with `compute_sqi` or `compute_sqi_windowed`, and optionally run PPG-specific tools such as `preprocess_ppg`.

### Step 3 — Loading and Optional Preprocessing
The agent calls `load_signal_file` to load waveform samples from the configured file and column. For PPG signals that need cleanup, the agent calls `preprocess_ppg` to filter, normalize, and detect peaks. The agent logs the loading and preprocessing parameters applied.

### Step 4 — Windowed Quality Analysis
The agent calls `compute_sqi_windowed` with the configured window duration (default 30 seconds). For a 1-hour recording at 30-second windows, this produces approximately 120 window-level quality results. Segment boundaries and metadata are stored in the `Segments` table.

### Step 5 — SQI Computation
The agent calls `compute_sqi` for overall quality and `compute_sqi_windowed` for segment-level quality. These tools return overall and per-window quality scores that are persisted to the `SQIResults` table.

### Step 6 — Classification
The agent applies the configured rule dictionary to overall and windowed SQI scores, and calls `check_clinical_thresholds` when heart rate, SpO2, or SQI thresholds need structured flags. Classification results are written to the `Classifications` table.

### Step 7 — Agent Interpretation
The LLM reads the classification results and SQI matrix. It reasons about patterns: overall acceptance rate, clusters of consecutive rejected segments, temporal degradation trends (e.g., signal quality declining in the final 20 minutes), and outlier SQI values. The agent produces a structured interpretation object.

### Step 8 — Report Generation
The backend report service combines SQI summary statistics, the agent's interpretation text, the timeline of accepted/rejected segments, flagged issues, and actionable recommendations into a canonical JSON report payload. HTML and PDF reports are rendered exports from that JSON payload.

### Step 9 — Dashboard Display
The frontend polls `GET /api/results/{recording_id}` at 5-second intervals until status is `completed`. Live waveform streaming and SSE-based real-time progress are deferred to post-MVP/future work. Two views are updated:
- **Monitoring View**: The waveform is rendered with color-coded quality overlay (green = accepted, red = rejected) per segment. Rejected segments are visually highlighted.
- **Dashboard View**: Summary scores (acceptance rate, overall quality score), a 2D heatmap of SQI values across segments, and any active alerts are displayed.

### Step 10 — Chatbot
A clinician or researcher can ask natural-language questions about the assessment through the chatbot interface (e.g., "Why was segment 45 rejected?"). The `POST /api/chat` endpoint routes the message to the agent, which retrieves the relevant segment detail and SQI breakdown and generates a plain-language explanation.

---

## 5. Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser Client                           │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────────┐ │
│  │  Upload Page │  │  Dashboard    │  │  Monitoring View      │ │
│  └──────┬───────┘  └──────┬────────┘  └───────────┬───────────┘ │
└─────────┼─────────────────┼─────────────────────────┼───────────┘
          │    HTTP/REST     │                         │
          ▼                 ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Next.js + React Frontend  (port 3000)              │
│            app/ │ components/ │ services/ (API clients)         │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP REST  (JSON)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                FastAPI Backend  (port 8000, Python 3.11)        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   API Routers (api/)                     │    │
│  │  /upload │ /assess │ /results │ /reports │ /dashboard   │    │
│  │  /chat                                                   │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │                  Services Layer (services/)              │    │
│  │  FileService │ ReportService │ DashboardService          │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │                   Agent Layer (agent/)                   │    │
│  │              smolagents Tool Orchestrator                 │    │
│  │     ┌──────────────────────────────────────────────┐    │    │
│  │     │              Tool Registry (tools/)           │    │    │
│  │     │  load_signal │ compute_sqi │ compute_windowed │    │    │
│  │     │  preprocess_ppg │ hrv │ spo2 │ thresholds       │    │    │
│  │     │  (Python function calls → OUCRU tools)       │    │    │
│  │     └──────────────────────┬───────────────────────┘    │    │
│  │                            │ direct Python imports        │    │
│  │     ┌──────────────────────▼───────────────────────┐    │    │
│  │     │         vital_sqi library (Python 3.11)       │    │    │
│  │     │  load_signal_file() │ compute_sqi()          │    │    │
│  │     │  compute_sqi_windowed() │ preprocess_ppg()  │    │    │
│  │     │  HRV, SpO2, DC-layer, threshold helpers       │    │    │
│  │     └──────────────────────┬───────────────────────┘    │    │
│  │                            │                             │    │
│  │     ┌──────────────────────▼───────────────────────┐    │    │
│  │     │          Local Ollama LLM Runtime             │    │    │
│  │     │  Qwen3-8B for workflow/report/Q&A reasoning   │    │    │
│  │     └──────────────────────┬───────────────────────┘    │    │
│  └──────────────────────────── │ ──────────────────────────┘    │
│                                │                                 │
└────────────────────────────────┼─────────────────────────────────┘
                                 │ External API / Internal network
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                 LLM Providers (external)                        │
│  Ollama :11434 + Qwen3-8B                                     │
│  Local-first workflow planning, report explanation, and Q&A    │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐   ┌──────────────────────────────┐
│      PostgreSQL Database     │   │       File Storage           │
│  Recordings │ Segments       │   │  Raw waveform files (EDF/WFDB/CSV)│
│  SQIResults │ Classifications│   │  Preprocessed artifacts      │
│  Reports    │ AgentLogs      │   │  Generated PDF/HTML reports  │
└─────────────────────────────┘   └──────────────────────────────┘
```

---

## 6. Why This Hybrid Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Signal processing | Python 3.11 | `vital_sqi` runs in the same process as FastAPI — no version conflict |
| Agent framework | Python (smolagents) | Lets the LLM select approved Python tools while keeping execution constrained to registered analysis functions |
| LLM inference | Ollama + Qwen3-8B | Local-first workflow planning, report explanation, and Q&A without relying on external LLM APIs |
| Frontend | Next.js + React + Tailwind CSS | Type safety catches API contract bugs at compile time; Next.js provides routing and production-ready frontend structure |
| API contract | REST/JSON | Simple, stateless, and easy to test; no need for GraphQL complexity at this project scale |
| Orchestration | Docker Compose | Minimal operational overhead for a capstone project; reproducible local environments |

The REST API boundary means the frontend and backend teams can work independently as long as the API contract (defined in [API Specifications](03-api-specifications.md)) is respected. Either service can be replaced or upgraded without touching the other.

---

## Docker Compose Services

| Service | Image Base | Port | Required | Description |
|---------|-----------|------|----------|-------------|
| `frontend` | node:20-alpine | 3000 | Yes | Next.js + React frontend |
| `backend` | python:3.11-slim | 8000 | Yes | FastAPI + smolagents + OUCRU signal tools |
| `db` | postgres:15-alpine | 5432 | Yes | PostgreSQL database |
| `ollama` | ollama/ollama | 11434 (internal) | Yes | Local Qwen3-8B LLM runtime |

> **Note:** Ollama runs Qwen3-8B for local-first workflow planning, report explanation, and Q&A.

All services communicate over a shared Docker bridge network (`vital-network`). Only `frontend` (3000) and `backend` (8000) ports are exposed to the host. The `ollama` and `db` services are internal-only.

---

## 7. Deployment Architecture

### Local Development
- `docker compose up` starts all required services (frontend, backend, db, ollama)
- Hot reload enabled for frontend (Next.js) and backend (uvicorn --reload)
- Set the Ollama model to Qwen3-8B in `config.yaml`
- Ollama serves the local LLM runtime used by smolagents

### Production (Google Cloud)

| Component | GCP Service | Notes |
|-----------|-------------|-------|
| Frontend | Cloud Run (static) or GCS + Cloud CDN | Next.js frontend served as container or static/exported files where applicable |
| Backend | Cloud Run | Auto-scaling; FastAPI + smolagents + OUCRU signal tools in one container |
| LLM Runtime | Cloud Run service or managed VM for Ollama | Hosts Qwen3-8B for local-first agent workflows |
| Database | Cloud SQL (PostgreSQL 15) | Managed, automated backups |
| File Storage | Google Cloud Storage (GCS) | Uploaded recordings and generated reports |

Budget: $2,000–$3,000 GCP credits (expires August 23, 2026). See [Tech Stack](05-tech-stack.md) for detailed cost analysis.
