# 08 — System Architecture

[← Back to Index](00-index.md)

---

**Scope:** This architecture addresses waveform data (ECG, PPG) only. Imaging data quality monitoring is deferred to future phases per project scope decisions.

---

## 1. High-Level Architecture Overview

The system is organized as a **monorepo** containing a Python backend and a TypeScript frontend. The frontend communicates with the backend via REST. Both services are independently containerized and orchestrated via Docker Compose.

**Design rationale:**
- `vital_sqi` supports Python >=3.7 (tested on 3.11), so it runs directly in the same backend container alongside FastAPI and LangGraph. No separate microservice is needed.
- TypeScript/React provides a modern, type-safe dashboard with strong ecosystem support.
- REST over HTTP keeps every contract simple, well-documented, and language-agnostic.
- Monorepo simplifies dependency management, shared configuration, and CI/CD pipelines.

---

## 2. Monorepo Structure

```
vital-agent/
├── backend/                  # Python 3.11 — FastAPI + Agent + vital_sqi
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── agent/            # LangGraph agent logic
│   │   ├── tools/            # Thin wrappers calling vital_sqi directly (Python imports)
│   │   ├── services/         # Report generation, data processing
│   │   └── api/              # REST endpoint definitions
│   ├── requirements.txt      # Includes vital_sqi + all dependencies
│   └── Dockerfile
├── frontend/                 # TypeScript — React + Vite
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── services/
│   ├── package.json
│   └── Dockerfile
├── docs/
├── docker-compose.yml
└── README.md
```

### Key directory notes

| Directory | Responsibility |
|-----------|---------------|
| `backend/app/agent/` | All LLM orchestration logic; state machine, prompt templates, decision loops |
| `backend/app/tools/` | Thin Python wrappers that call `vital_sqi` functions directly — standard Python imports, no HTTP overhead |
| `backend/app/services/` | Business logic decoupled from HTTP: report generation, file parsing, DB access |
| `backend/app/api/` | FastAPI routers; no business logic — delegates immediately to services or agent |
| `frontend/src/services/` | All HTTP calls to the backend; typed request/response interfaces |

---

## 3. Communication Pattern

```
Browser
  ↓  (HTTP/HTTPS)
React + Vite Frontend  (port 3000)
  ↓  (HTTP REST API)
FastAPI Backend  (port 8000, Python 3.11)
  ├──→ vital_sqi library  (direct Python imports)
  ├──→ (Token-Encoding Layer) → Gemini API (Vertex AI) [primary]
  ├──→ (Token-Encoding Layer) → Ollama (port 11434) [optional fallback]
  └──→ PostgreSQL  (port 5432)
```

The **token-encoding privacy layer** sits between the agent and every external LLM call. Before sending a prompt, the agent encodes patient-identifiable tokens (subject IDs, device IDs, timestamps) using a reversible mapping stored in memory for the duration of the request. The LLM receives and reasons over anonymized tokens only. When the LLM response is received, the layer decodes the tokens back before the response is returned to the rest of the system. This ensures no raw patient identifiers leave the FastAPI process.

- The browser communicates only with the frontend service (React + Vite).
- The frontend calls the FastAPI backend via typed REST endpoints.
- FastAPI delegates assessment requests to the LangGraph agent.
- The backend imports `vital_sqi` directly as a Python package — no inter-service HTTP calls needed since `vital_sqi` supports Python 3.11.
- Results flow back up the chain and are persisted to PostgreSQL and file storage before being returned to the client.

---

## 4. Application Flow (10 Steps)

### Step 1 — Data Upload
The researcher uploads a waveform file (1–2 hour ECG or PPG recording) through the web dashboard. Supported formats: ECG — EDF, MIT/WFDB, CSV; PPG — CSV. The frontend sends a `POST /api/upload` multipart request carrying the file and metadata (signal type, sampling rate). The backend validates the file, stores it in object storage, and creates a `Recording` record in PostgreSQL with status `uploaded`.

### Step 2 — Agent Activation
The backend publishes a processing job (or directly calls the agent service). The agent is instantiated and receives a context object containing the recording ID, file path, signal type, and sampling rate. The agent uses the configured LLM provider (Gemini 2.0 Flash via Vertex AI by default; Ollama as optional fallback) to reason about which processing pipeline to invoke: ECG pipeline (`assess_ecg_quality`) or PPG pipeline (`assess_ppg_quality`).

### Step 3 — Preprocessing
The agent calls the `preprocess_signal` tool, which wraps `vital_sqi`'s bandpass filter, trim, and smoothing functions. The preprocessed signal is stored as an intermediate artifact. The agent logs the preprocessing parameters applied.

### Step 4 — Segmentation
The agent calls `vital_sqi`'s `segment_split` function with the configured window duration (default 30 seconds). For a 1-hour recording at 30-second windows, this produces approximately 120 segments. Segment boundaries and metadata are stored in the `Segments` table.

### Step 5 — SQI Computation
The agent calls `compute_ecg_sqis()` (for ECG) or `compute_ppg_sqis()` (for PPG). These functions return a table of dimensions `segments × SQI metrics` — up to 47+ SQI values per segment, including kurtosis, skewness, SNR, and clinical metrics such as mean HR and SDNN. The SQI matrix is persisted to the `SQIResults` table.

### Step 6 — Classification
The agent calls `assess_ecg_quality()` or `assess_ppg_quality()`, which apply the configured rule dictionary to the SQI scores and produce an accept/reject classification for each segment. Classification results are written to the `Classifications` table.

### Step 7 — Agent Interpretation
The LLM reads the classification results and SQI matrix. It reasons about patterns: overall acceptance rate, clusters of consecutive rejected segments, temporal degradation trends (e.g., signal quality declining in the final 20 minutes), and outlier SQI values. The agent produces a structured interpretation object.

### Step 8 — Report Generation
The agent calls `generate_report`, which combines the SQI summary statistics, the agent's interpretation text, the timeline of accepted/rejected segments, flagged issues, and actionable recommendations into a structured report. The report is stored in both HTML and PDF formats.

### Step 9 — Dashboard Display
The frontend polls `GET /api/results/{recording_id}` at 5-second intervals until status is `completed`. Server-Sent Events (SSE) may be added in a later phase for real-time progress streaming. Two views are updated:
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
│               React + Vite Frontend  (port 3000)                │
│            pages/ │ components/ │ services/ (API clients)       │
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
│  │              LangGraph State Machine                     │    │
│  │     ┌──────────────────────────────────────────────┐    │    │
│  │     │              Tool Registry (tools/)           │    │    │
│  │     │  assess_ecg  │ assess_ppg │ preprocess_signal │    │    │
│  │     │  compute_sqis │ generate_report │ query_history│    │    │
│  │     │  (Python function calls → vital_sqi library) │    │    │
│  │     └──────────────────────┬───────────────────────┘    │    │
│  │                            │ direct Python imports        │    │
│  │     ┌──────────────────────▼───────────────────────┐    │    │
│  │     │         vital_sqi library (Python 3.11)       │    │    │
│  │     │  get_ecg_sqis() │ get_ppg_sqis()              │    │    │
│  │     │  get_qualified_ecg() │ get_qualified_ppg()    │    │    │
│  │     │  segment_split() │ preprocess functions       │    │    │
│  │     └──────────────────────┬───────────────────────┘    │    │
│  │                            │                             │    │
│  │     ┌──────────────────────▼───────────────────────┐    │    │
│  │     │     Token-Encoding Privacy Layer              │    │    │
│  │     │  Encodes PII tokens before LLM calls;         │    │    │
│  │     │  decodes responses before returning results   │    │    │
│  │     └──────────────────────┬───────────────────────┘    │    │
│  └──────────────────────────── │ ──────────────────────────┘    │
│                                │                                 │
└────────────────────────────────┼─────────────────────────────────┘
                                 │ External API / Internal network
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                 LLM Providers (external)                        │
│  Gemini 2.0 Flash via Vertex AI [primary]                      │
│  Ollama :11434 [optional fallback, docker profile: local-llm]  │
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
| Agent framework | Python (LangGraph) | LangChain ecosystem is Python-first; best tooling and community |
| LLM inference | Python (LangGraph + Vertex AI / Ollama) | Gemini via Vertex AI as primary (covered by GCP credits); Ollama self-hosted as optional fallback. Provider abstraction via `BaseLLMProvider` makes switching trivial. |
| Frontend | TypeScript / React + Vite | Type safety catches API contract bugs at compile time; Vite provides fast HMR and simple static builds; no SSR needed for a dashboard app |
| API contract | REST/JSON | Simple, stateless, and easy to test; no need for GraphQL complexity at this project scale |
| Orchestration | Docker Compose | Minimal operational overhead for a capstone project; reproducible local environments |

The REST API boundary means the frontend and backend teams can work independently as long as the API contract (defined in `10-api-specifications.md`) is respected. Either service can be replaced or upgraded without touching the other.

---

## Docker Compose Services

| Service | Image Base | Port | Required | Description |
|---------|-----------|------|----------|-------------|
| `frontend` | node:20-alpine | 3000 | Yes | React + Vite dev server (static build in prod) |
| `backend` | python:3.11-slim | 8000 | Yes | FastAPI + LangGraph + vital_sqi |
| `db` | postgres:15-alpine | 5432 | Yes | PostgreSQL database |
| `ollama` | ollama/ollama | 11434 (internal) | **No** (profile: `local-llm`) | Optional self-hosted LLM fallback |

> **Note:** Ollama is activated via Docker Compose profiles: `docker compose --profile local-llm up`. Default startup uses Gemini API (Vertex AI) and does not require the Ollama container.

All services communicate over a shared Docker bridge network (`vital-network`). Only `frontend` (3000) and `backend` (8000) ports are exposed to the host. The `ollama` and `db` services are internal-only.

---

## 7. Deployment Architecture

### Local Development
- `docker compose up` starts all 3 required services (frontend, backend, db)
- Hot reload enabled for frontend (Vite) and backend (uvicorn --reload)
- Set `LLM_PROVIDER=gemini` and `GOOGLE_CLOUD_PROJECT=<project-id>` in `.env` for Gemini API access
- To use Ollama locally instead: `docker compose --profile local-llm up` (pulls `llama3.1:8b` on first run)

### Production (Google Cloud)

| Component | GCP Service | Notes |
|-----------|-------------|-------|
| Frontend | Cloud Run (static) or GCS + Cloud CDN | Vite static build served as container or static files |
| Backend | Cloud Run | Auto-scaling; FastAPI + LangGraph + vital_sqi in one container |
| LLM (Gemini) | Vertex AI API | API call — no dedicated VM or GPU required |
| Database | Cloud SQL (PostgreSQL 15) | Managed, automated backups |
| File Storage | Google Cloud Storage (GCS) | Uploaded recordings and generated reports |

Budget: $2,000–$3,000 GCP credits (expires August 23, 2026). See [Tech Stack](13-tech-stack.md) for detailed cost analysis.
