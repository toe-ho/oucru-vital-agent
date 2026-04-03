# 14 — Development Phases

[← Back to Index](00-index.md)

---

## Overview

The project spans **16 weeks** (team-proposed timeline — to be confirmed with university supervisor and OUCRU) divided into 5 phases. Phases are sequential with defined dependency gates — a phase does not begin until its predecessor's deliverable is verified. A 1-week risk buffer is embedded in Phase 4. The final two weeks prioritize integration, deployment, and demo preparation over new feature development.

---

> **Scope Note:** This development plan addresses waveform data (ECG, PPG) only. Imaging data quality monitoring is deferred to future phases, per project scope decisions documented in [Goals and Non-Goals](../prd/03-goals-and-non-goals.md).

---

## Gantt-Style Timeline

```
Week  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │ 10  │ 11  │ 12  │ 13  │ 14  │ 15  │ 16  │
──────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
Ph 1  │█████│█████│█████│     │     │     │     │     │     │     │     │     │     │     │     │     │
Ph 2  │     │     │     │█████│█████│█████│█████│     │     │     │     │     │     │     │     │     │
Ph 3  │     │     │     │     │     │     │     │█████│█████│█████│█████│     │     │     │     │     │
Ph 4  │     │     │     │     │     │     │     │     │     │     │     │█████│█████│█████│     │     │
      │     │     │     │     │     │     │     │     │     │     │     │     │     │[BUF]│     │     │
Ph 5  │     │     │     │     │     │     │     │     │     │     │     │     │     │     │█████│█████│
──────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

[BUF] = Risk buffer week embedded in Phase 4 (Week 14)
```

---

## Phase Dependencies

```
Phase 1 (Foundation)
    │
    │ Gate: Docker Compose running, vital_sqi importable in backend container, DB migrations applied
    ▼
Phase 2 (Agent Core)
    │
    │ Gate: End-to-end API call processes a recording, results stored in DB
    ▼
Phase 3 (Web Dashboard) ◄── Depends on Phase 2 REST API contract being stable
    │
    │ Gate: Dashboard displays real assessment results from backend
    ▼
Phase 4 (Reporting & Refinement) ◄── Depends on Phase 3 UI components for report embedding
    │
    │ Gate: Reports generated, settings page functional, agent logs viewable
    ▼
Phase 5 (Delivery & Core Features)
    │
    └── Depends on all Phase 4 features being stable before deployment
```

---

## Phase 1: Foundation (Weeks 1–3)

**Goal:** Establish a working development environment with all core services running and `vital_sqi` integrated.

### Tasks

- [ ] **Monorepo setup**: Initialize repository with `/backend` (Python/FastAPI) and `/frontend` (React/Vite) directories. Configure shared `docker-compose.yml` at root.
- [ ] **Docker Compose**: Define services — `backend` (Python 3.11, includes vital_sqi), `frontend`, `postgres`. Add `ollama` as an optional service under the `local-llm` profile (`docker compose --profile local-llm up`). Default `docker compose up` uses Gemini API and does not require the Ollama container. Ensure all required services start with `docker compose up`.
- [ ] **CI/CD pipeline**: Configure GitHub Actions with jobs: `lint` (Ruff + ESLint), `test` (pytest + Vitest), `build` (Docker image builds). Pipeline must pass before merge to `main`.
- [ ] **vital_sqi integration**: Install `vital_sqi` (`pip install vitalSQI-toolkit`) directly in the backend container (Python 3.11). Run library's sample scripts against provided test EDF/CSV files. Verify all 4 pipeline functions (`get_ecg_sqis`, `get_ppg_sqis`, `get_qualified_ecg`, `get_qualified_ppg`) work with sample data on Python 3.11. Write a `vital_sqi_smoke_test.py` that calls the main segmentation and SQI functions and asserts expected output shapes.
- [ ] **FastAPI scaffolding**: Implement base app structure — routers, dependency injection, CORS config, health check endpoint (`GET /health`). Configure Pydantic Settings for environment variables.
- [ ] **Database setup**: Write SQLAlchemy models for all 6 tables (see `11-data-model.md`). Create Alembic migration files. Apply migrations via `alembic upgrade head` on container start.
- [ ] **Frontend scaffolding**: Initialize Vite + React + TypeScript project. Configure Tailwind CSS and shadcn/ui. Set up React Router v6 with placeholder routes for all 6 screens. Implement global navigation bar component.
- [ ] **Basic file upload endpoint**: `POST /api/upload` — accepts multipart file, validates extension and size, stores to filesystem, creates `recordings` row with status `uploaded`.

### Deliverable

All 3 required services (`backend`, `frontend`, `db`) run via `docker compose up`. A signal file can be uploaded via `POST /api/upload` and the resulting row is visible in PostgreSQL. `vital_sqi` functions are importable and callable from within the backend container without errors.

### Success Criteria

- [ ] `docker compose up` starts all services without manual intervention
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /api/upload` returns `201` with a recording UUID
- [ ] `vital_sqi_smoke_test.py` passes against a sample 10-second ECG file
- [ ] All Alembic migrations apply cleanly on a fresh database
- [ ] CI pipeline passes on `main` branch

---

## Phase 2: Agent Core (Weeks 4–7)

**Goal:** Build the full agentic analysis pipeline — from uploaded recording to classified segments with SQI results stored in the database.

### Tasks

- [ ] **Tool wrappers (8 functions)**: Implement thin Python wrappers that call `vital_sqi` functions via direct Python imports (no HTTP). Each wrapper takes typed parameters, calls the relevant `vital_sqi` function, and returns a structured dict. Functions:
  1. `assess_ecg_quality(file_path, sampling_rate, ...)` — run full ECG pipeline: preprocess, segment, compute SQIs, classify
  2. `assess_ppg_quality(file_path, sampling_rate, ...)` — equivalent full PPG pipeline
  3. `compute_ecg_sqis(file_path, sampling_rate, ...)` — compute ECG SQI scores only, no classification
  4. `compute_ppg_sqis(file_path, sampling_rate, ...)` — compute PPG SQI scores only, no classification
  5. `preprocess_signal(file_path, sampling_rate, signal_type, ...)` — bandpass filter, trim, baseline wander removal
  6. `generate_report(recording_id, assessment_result, agent_interpretation, ...)` — compile and persist quality report
  7. `query_history(subject_id, device_id, ...)` — fetch past assessment results for trend analysis
  8. `get_segment_detail(recording_id, segment_id)` — retrieve full SQI breakdown and waveform data for a segment
- [ ] **LangGraph agent setup**: Define agent state schema. Implement ReAct loop as a LangGraph `StateGraph` with nodes: `analyze_metadata`, `preprocess`, `run_pipeline`, `interpret_results`, `fetch_details`, `generate_report`, `finalize_or_escalate`. Register all 8 tool wrappers.
- [ ] **LLM provider abstraction layer**: Implement `BaseLLMProvider` abstract class (`backend/app/agent/llm/base_provider.py`) with `invoke()`, `stream()`, and `get_model_name()` methods. Implement `GeminiProvider` (primary, via `langchain-google-vertexai`) and `OllamaProvider` (optional fallback). Implement `get_llm_provider()` factory function reading `LLM_PROVIDER` env var (default: `gemini`). Write system prompt that instructs the model to use tools for data retrieval and avoid hallucinating metric values. Test tool-calling with Gemini 2.0 Flash via Vertex AI.
- [ ] **Processing endpoint**: `POST /api/assess` — triggers agent as a background task. Updates `recordings.status` to `processing`. On completion, sets status to `completed` or `failed`.
- [ ] **Results storage**: After each segment is processed, persist `segments` row and all `sqi_results` rows. Persist `agent_logs` rows for each tool call made by the agent.
- [ ] **Status polling endpoint**: `GET /api/results/{recording_id}` — returns current status and progress percentage (segments processed / total segments).
- [ ] **Results retrieval endpoints**: `GET /api/results/{recording_id}` — list all segments with classification and quality score. `GET /segments/{id}/sqi` — list all SQI results for one segment.

### Deliverable

A single API call to `POST /api/assess` triggers the agent, which loads the file, segments it, computes SQI metrics for each segment, classifies each segment, and stores all results in PostgreSQL. The agent logs every tool call. LLM provider abstraction layer (`BaseLLMProvider`) is in place — switching between Gemini and Ollama requires only changing the `LLM_PROVIDER` environment variable.

### Success Criteria

- [ ] End-to-end pipeline completes on a 10-minute ECG file within 5 minutes
- [ ] All segment rows created with non-null `classification` values
- [ ] `sqi_results` rows created for every metric on every segment
- [ ] `agent_logs` rows created for every tool call
- [ ] `GET /api/results/{recording_id}` returns correct segment count
- [ ] pytest integration tests cover the full pipeline with a fixture recording

---

## Phase 3: Web Dashboard (Weeks 8–11)

**Goal:** Build a fully functional frontend that displays real assessment results from the Phase 2 API.

### Tasks

- [ ] **Upload Page** (Screen 1): Implement drag-and-drop file upload with `react-dropzone`. Signal type radio and sampling rate input. On submit, call `POST /api/upload` then `POST /api/assess`. Poll `GET /api/results/{recording_id}` every 2 seconds and show progress. Redirect to Monitoring Screen on completion.
- [ ] **TanStack Query setup**: Configure `QueryClient`. Create typed query hooks for all API endpoints: `useRecording`, `useSegments`, `useSqiResults`, `useAgentLogs`, `useSettings`.
- [ ] **Monitoring Screen** (Screen 2): Implement Plotly.js waveform display. Fetch raw signal data from `GET /api/recordings/{recording_id}/waveform?start=0&end=60&downsample=5000` (returns downsampled channel data). Render color-coded segment overlay. Segment navigation with prev/next buttons and dropdown. SQI scores panel updates on segment change.
- [ ] **Waveform endpoint**: `GET /api/recordings/{recording_id}/waveform` — backend reads the original file via `vital_sqi`, returns downsampled channel data to max 10000 points (configurable via `downsample` query param) for browser rendering.
- [ ] **Quality Dashboard** (Screen 3): Implement summary KPI cards, accept/reject bar chart, timeline heatmap (one div per segment, colored by classification). Alerts panel populated from segments where `quality_score < 0.4`. Recent recordings table.
- [ ] **API integration**: All data fetched from real backend endpoints. No mock data in production code. Loading skeletons shown during fetch. Error states handled with retry buttons.
- [ ] **Routing and navigation**: All 6 routes functional. Active route highlighted in nav bar. Browser back/forward navigation works correctly.

### Deliverable

The full dashboard renders real assessment results. A user can upload a file, watch it process, view the waveform with quality overlay, inspect per-segment SQI scores, and see the quality summary dashboard — all populated from live data.

### Success Criteria

- [ ] Waveform renders for a 10-minute ECG file in under 3 seconds
- [ ] Color-coded segment overlay matches `segments.classification` values in DB
- [ ] All 4 KPI cards show correct counts matching DB
- [ ] Timeline heatmap renders all segments in correct order
- [ ] Segment navigation updates waveform view and SQI panel without page reload
- [ ] Vitest component tests cover Upload Page and Monitoring Screen

---

## Phase 4: Reporting & Refinement (Weeks 12–14, with buffer)

**Goal:** Add automated report generation, system configurability, and agent transparency. Week 14 is a risk buffer — use it for feature completion, bug fixes, or performance work as needed.

### Tasks

- [ ] **Report generation endpoint**: `POST /api/assess` (report step) — agent generates a structured report using `content_json` schema: `{summary, timeline, flagged_segments[], recommendations[]}`. Renders to HTML using a Jinja2 template. Optionally exports to PDF via `weasyprint`.
- [ ] **Report Viewer** (Screen 4): Fetch and render report HTML. Embed timeline chart (Plotly). Flagged segments table. Export buttons (PDF download, HTML download, print).
- [ ] **Agent interpretation improvements**: Enhance system prompt to produce: (1) per-segment natural language explanation of rejection reason, (2) recording-level pattern detection (e.g., "quality degrades after minute 3"), (3) actionable recommendations. Test with 5 diverse recordings.
- [ ] **Settings Page** (Screen 5): Implement threshold configuration table with inline editing. Segmentation config controls. `PUT /api/settings/thresholds` endpoint. Import/Export JSON buttons. Reset to defaults with confirmation dialog.
- [ ] **Agent logs viewer**: Add a collapsible panel in the Monitoring Screen (or a separate `/recordings/:id/logs` route) that shows the agent's step-by-step tool calls and reasoning for the current recording.
- [ ] **Performance optimization**: Profile end-to-end pipeline. If processing a 30-minute recording exceeds 10 minutes, investigate parallelizing SQI computation across segments using `asyncio.gather` or `ProcessPoolExecutor`.
- [ ] **[Buffer — Week 14]**: Resolve accumulated technical debt, fix bugs from user testing, improve error handling and edge case coverage. No new features planned for this week.

### Deliverable

Automated HTML/PDF reports are generated per recording. The Settings page allows threshold configuration that immediately affects subsequent analyses. Agent reasoning is visible in the UI. System is stable with no known critical bugs.

### Success Criteria

- [ ] Report endpoint returns a report within 60 seconds for a 10-minute recording
- [ ] Report HTML renders correctly in browser and as exported PDF
- [ ] Changing an SQI threshold in Settings affects classification in a new analysis run
- [ ] Agent logs viewer shows correct tool call sequence matching `agent_logs` table
- [ ] pytest test suite has ≥70% coverage on backend business logic

---

## Phase 5: Delivery & Core Features (Weeks 15–16)

**Goal:** Polish, deploy, and prepare the prototype for the capstone presentation. Deliver chatbot and token-encoding as core features alongside deployment and demo preparation.

### Tasks

- [ ] **Chatbot interface**: Implement Screen 6. Backend endpoint `POST /api/chat` accepts a message + `recording_id`, invokes the agent with conversational context, returns a natural language response. Frontend chat panel with suggested questions. Chatbot must be able to answer questions about segment rejection reasons and SQI explanations.
- [ ] **Token-encoding privacy layer**: Implement pseudonymization of patient identifiers in filenames and metadata before storage. Configurable via Settings. Reversible with a stored mapping table. Encoding applied before any data leaves the system boundary (e.g., before external LLM calls).
- [ ] **End-to-end testing**: Manual QA pass on all 6 screens including chatbot. Run full pipeline on at least 3 diverse recordings (different signal types, durations, quality levels). Fix any bugs found.
- [ ] **Documentation finalization**: Update `README.md` with setup instructions. Finalize all `./docs/prd/` files. Write `docs/vital-sqi-compatibility-patches.md` if any patches were applied.
- [ ] **GCP deployment**: Deploy backend to Cloud Run. Deploy frontend static bundle to Cloud Run (nginx). Provision Cloud SQL PostgreSQL. Enable Vertex AI API and configure `GOOGLE_CLOUD_PROJECT` and `LLM_PROVIDER=gemini` via Secret Manager — no GPU VM required. Set up all environment variables and secrets via Secret Manager.
- [ ] **Demo preparation**: Prepare a 5-minute demo script using a real OUCRU ECG/PPG dataset. Rehearse the upload → process → monitor → report → chat flow. Prepare slide deck for presentation.

### Deliverable

A polished, deployed prototype accessible via a public Cloud Run URL. Chatbot interface and token-encoding privacy layer are functional and demonstrated. Full demo flow rehearsed and ready. All documentation complete.

### Success Criteria

- [ ] Application accessible at a live GCP URL
- [ ] Full pipeline demo completes without errors on presentation day
- [ ] Report generation produces a presentable PDF output
- [ ] All known critical and high-severity bugs resolved
- [ ] `docker compose up` still works for local development after cloud deployment
- [ ] Chatbot (`POST /api/chat`) returns accurate, context-grounded responses about segment rejection and SQI scores for a given recording
- [ ] Token-encoding layer encodes patient identifiers before storage and before any external LLM call; decoding via stored mapping is verified correct

---

## Risk Register

See [Risk Assessment](15-risk-assessment.md) for the full risk register. The authoritative list of risks, likelihood ratings, mitigations, and contingencies is maintained there.

---

## Definition of Done (per phase)

A phase is considered complete when:
1. All tasks in the todo list are checked off
2. The deliverable is demonstrated working end-to-end
3. All success criteria pass
4. CI pipeline passes on `main` branch (lint + tests)
5. A brief phase completion note is added to `docs/project-changelog.md`
