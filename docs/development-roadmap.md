# Development Roadmap

**Status:** In Progress  
**Last Updated:** 2026-05-29  
**Completed Phases:** 1-7 of 8

## Overview

This living document tracks the OUCRU Vital Agent implementation progress from PRD to deployable prototype. The system monitors waveform data quality for ECG and PPG signals using signal quality indices (SQI) with agentic interpretation.

## Phase Status

### Phase 1: Repository Foundation ✓ Complete (2026-05-29)

**Goal:** Reproducible monorepo skeleton with single-command local startup.

**Completed:**
- README.md and CLAUDE.md with project guidance
- FastAPI backend skeleton with health endpoint
- Next.js 14 App Router frontend with Tailwind and TanStack Query
- Docker Compose (postgres, ollama, backend, frontend)
- Makefile with `up`, `down`, `lint`, `test` shortcuts
- GitHub Actions CI (backend lint/test, frontend lint/build)
- No hardcoded secrets

**Deliverables:**
- `/home/tuan_crypto/projects/oucru-capstone/README.md`
- `/home/tuan_crypto/projects/oucru-capstone/CLAUDE.md`
- `/home/tuan_crypto/projects/oucru-capstone/Makefile`
- `/home/tuan_crypto/projects/oucru-capstone/docker-compose.yml`
- Backend: `main.py`, health router, settings, error handlers
- Frontend: App router, layout, page scaffolds, API client skeleton

---

### Phase 2: Backend Platform ✓ Complete (2026-05-29)

**Goal:** Database, authentication, storage, settings, and audit infrastructure.

**Completed:**
- SQLAlchemy 2.0 async models (User, Role, Recording, AssessmentJob, Segment, SqiResult, Report, ChatMessage, AgentLog, AuditEvent, Setting)
- Alembic migrations (initial schema with constraints and indexes)
- Google OAuth/JWT auth flow with role-based access control
- Storage service abstraction (local filesystem dev, GCS adapter ready)
- Settings service (persistent threshold configuration)
- Audit service with request ID middleware
- Error response standardization: `{error, detail, request_id}`
- Role guards: `admin`, `researcher`, `reviewer`, `readonly`

**Deliverables:**
- Database models in modular files (user, recording, assessment, report, chat, log)
- Auth dependencies with role enforcement
- Settings endpoints: `GET/PUT /api/settings/thresholds`
- Audit event logging for all mutations

---

### Phase 3: Signal Ingestion & SQI Tools ✓ Complete (2026-05-29)

**Goal:** Accept waveform files, validate metadata, expose vital_sqi wrappers.

**Completed:**
- File upload endpoints: `POST /api/recordings/upload`, `POST /api/recordings/batch-upload` (50 max)
- CSV/Parquet support (EDF/WFDB deferred post-MVP)
- Single-channel validation per file (multi-channel post-MVP)
- Path traversal prevention and checksum verification
- Signal metadata: format, size, sampling rate, duration, channel info
- 8 approved tool wrappers with vital_sqi integration
- `SignalRef` pattern: large arrays never exposed to agent/LLM
- Recording retrieval: `GET /api/recordings`, `GET /api/recordings/{id}`
- Synthetic ECG/PPG test fixtures

**Tools Wrapped:**
- `load_signal_file`, `compute_sqi`, `compute_sqi_windowed`
- `preprocess_ppg`, `extract_hrv_features`, `estimate_spo2`, `extract_ppg_dc_layer`, `check_clinical_thresholds`

**Deliverables:**
- Upload/batch-upload routers
- File validators (format, size, headers, channels)
- Tool wrappers with graceful error handling and fallback
- Test fixtures for ECG/PPG signals

---

### Phase 4: Assessment Agent Pipeline ✓ Complete (2026-05-29)

**Goal:** Process recordings into assessment jobs, segments, SQI results, and agent logs.

**Completed:**
- `POST /api/assess` async background job creation
- Deterministic windowed SQI computation with configurable segment duration
- smolagents `ToolCallingAgent` with Ollama (Qwen3-8B)
- Segment creation with immutable AI classification
- SQI result persistence with threshold comparisons
- Agent log recording (tool calls, reasoning, structured output)
- Rule-based fallback when LLM unavailable
- Job status tracking: queued, processing, completed, failed, cancelled
- Endpoints: `GET /api/assess/{id}`, `/results`, `/logs`, `/segments/{segId}`
- `config.yaml` for assessment workflow parameters

**Deliverables:**
- Assessment service with background task orchestration
- Agent orchestrator with tool registry
- Segment classification service with rule evaluation
- Agent log service (compact summaries, no raw waveforms)
- Assessment API with status/results/logs/segments queries

---

### Phase 5: Reporting & Feedback Governance ✓ Complete (2026-05-29)

**Goal:** Canonical reports and segment feedback without mutating original AI outputs.

**Completed:**
- Report JSON schema v1.0 (summary, timeline, flagged segments, recommendations, limitations)
- Automatic report generation on assessment completion
- HTML and PDF export (WeasyPrint)
- Segment override API: `POST /api/segments/{id}/overrides`
- Override supersede pattern (append-only event table)
- Report freshness detection (stale when overrides postdate generation)
- Effective classification helper: override else AI classification
- RBAC for overrides: `reviewer`, `admin` only
- Endpoints: `GET /api/reports/{id}`, `/freshness`, `/export/html`, `/export/pdf`
- `GET /api/segments/{id}/effective-classification`
- Audit events for all mutations

**Deliverables:**
- Report service with JSON schema generation
- Report rendering service (HTML/PDF)
- Segment override service with append-only design
- Report freshness service
- Feedback/learning service (candidate/approval/rollback workflow)

---

### Phase 6: Practitioner Dashboard ✓ Complete (2026-05-29)

**Goal:** Role-aware web interface for upload, monitoring, reports, and settings.

**Completed:**
- API client with auth interceptors and error handling
- TypeScript types for all domain entities
- Upload page: drag-drop, single/batch upload, validation, progress tracking
- Waveform viewer (Recharts) with segment overlays
- Segment timeline and SQI scores panel
- Override panel (reviewer/admin only, role checks)
- Report viewer with stale warning banner
- Settings page for threshold configuration
- Agent log viewer with collapsible entries
- Dashboard with KPI cards, ratios, alerts
- Navigation with auth context
- WCAG 2.1 AA accessibility target

**Pages:**
- `/dashboard` - KPI summary and recent uploads
- `/upload` - File upload with drag-drop
- `/recordings/[id]/monitor` - Waveform, segments, SQI, overrides
- `/recordings/[id]/report` - Report viewer, export buttons, stale warning
- `/settings` - Threshold and workflow configuration
- `/login` - Google OAuth flow

**Components:**
- FileUploadDropzone, WaveformViewer, SegmentTimeline, SqiScoresPanel
- SegmentOverridePanel, ReportViewer, ChatbotPanel
- QueryProvider for TanStack Query integration

**Deliverables:**
- Frontend routes and page scaffolds
- API client (services/api-client.ts)
- Query hooks for all domains
- UI components with accessibility

---

### Phase 7: Grounded Chatbot ✓ Complete (2026-05-29)

**Goal:** Answer practitioner questions using persisted SQI and assessment data.

**Completed:**
- Chat endpoint: `POST /api/chat`
- Conversation and message persistence (ChatMessage with sources)
- Grounding service retrieves recording context (50-segment max, no raw arrays)
- Ollama-grounded responses (Qwen3-8B) with fallback templates
- Question classifier for intents: segment reason, quality, metric counts, terminology, override explanation
- Constrained system prompt forbidding unsupported values
- Deterministic response templates for common intents
- Message sources tracking for auditability
- Frontend chat page `/chat` with recording selector
- Chatbot panel component with suggested questions
- Markdown rendering and loading/error states

**Deliverables:**
- Chat router and service
- Chat grounding service
- Conversation/message repositories
- Agent prompts with grounding constraints
- Frontend chat page and components

---

### Phase 8: Verification & Demo ⏳ Pending

**Goal:** Validate acceptance criteria, prepare demo dataset, document deployment.

**Tasks:**
- Run full test suite (backend unit/integration, frontend component/e2e)
- Benchmark 1-hour recording on target hardware
- Verify AC-001 through AC-021 with golden-file tests
- Prepare 5-10 anonymized OUCRU benchmark recordings
- Write deployment guide (local Docker, cloud options)
- Record demo walkthrough
- Performance profiling and optimization

**Target Completion:** 2026-06-05

---

## Key Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Backend LOC | < 10K | ~8.5K (56 Python files) |
| Frontend LOC | < 8K | ~6.8K (27 TypeScript files) |
| Test coverage | > 80% | 63 tests passing |
| Assessment latency (1h) | < 10 min | TBD (Phase 8) |
| API response time | < 500ms | TBD (Phase 8) |
| Uptime | > 99% | TBD (production) |

---

## Critical Dependencies

- **vital_sqi library:** Core signal quality computation (pinned version)
- **Ollama:** Local LLM inference (Qwen3-8B model pull required)
- **PostgreSQL:** Persistent data store
- **Docker Compose:** Local development baseline
- **Next.js 14:** Frontend framework with App Router

---

## Known Deferred Tasks

- **EDF/MIT-WFDB support:** Post-MVP (Phase 3 deferred)
- **Multi-channel ECG:** Post-MVP (Phase 3 deferred)
- **Cloud deployment:** Optional (local Docker is MVP)
- **CodeAgent use:** Security review required (ToolCallingAgent only)
- **5-10 OUCRU benchmark recordings:** Pending availability
- **Automated model retraining:** Feedback promotion is staged only

---

## Architecture Summary

```
User (Google OAuth) → Frontend → Backend API → Database
                                → Storage Service → File System
                                → Agent Services → Ollama LLM
                                → Report Services → PDF/HTML
```

**Data Flow:**
1. Upload → Ingestion validation → Recording stored + metadata
2. Assess → SQI computation → Segments + results → Agent interpretation → Logs
3. Report → Auto-generation → JSON → HTML/PDF render
4. Override → Segment review → Append-only event → Effective classification
5. Chat → Context retrieval → LLM grounding → Message persistence

---

## Success Criteria (Acceptance)

**AC-001:** Upload to report with zero manual steps ✓ Phase 5  
**AC-002:** 1-hour assessment < 10 minutes ⏳ Phase 8  
**AC-003:** Dashboard load < 3 seconds ⏳ Phase 8  
**AC-004:** Report sections complete ✓ Phase 5  
**AC-005:** 100% tool invocations logged ✓ Phase 4  
**AC-006–021:** Full acceptance criteria suite ⏳ Phase 8  

---

## Next Steps

1. Complete Phase 8 verification with golden-file tests
2. Obtain OUCRU benchmark recordings
3. Prepare deployment guide and demo walkthrough
4. Schedule team review and stakeholder demo
5. Plan post-MVP roadmap (cloud deployment, additional formats, multi-modal)
