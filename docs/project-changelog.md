# Project Changelog

**Latest Update:** 2026-05-30  
**All Versions Below**

---

## [2026-05-30] — UI/UX Redesign & Brand Alignment

### Frontend Redesign (7-phase)
- **Design tokens:** Full CSS-var token system in `globals.css` (light + `.dark`); `tailwind.config.ts` mapped; Inter + JetBrains Mono loaded via `next/font`. Clinical status tokens: exact emerald-500/red-500/amber-500.
- **shadcn/ui primitives:** Button, Card, Badge, Input, Textarea, Table, Dialog, Tooltip, Tabs, Select, Skeleton, Sonner added; `ThemeProvider` with no-flash dark mode; `cn()` utility.
- **App shell:** Persistent sidebar (desktop) + mobile drawer; brand logo lockup (abstract monoline peak glyph); breadcrumbs, theme toggle, user/sign-out in topbar; shared `LoadingState`/`EmptyState`/`ErrorState` with `03` microcopy.
- **Core verdict surfaces:** `ClassificationBadge` with icon+text+aria (SC 1.4.1); `SegmentTimeline` using token status colors + indigo selection/hover; `SqiScoresPanel` with mono tabular-nums + pass/fail icon+aria-live; monitor page verdict-first hierarchy; report-viewer exact stale copy.
- **Vital Agent chat:** Renamed from "Quality Assistant"; user bubble indigo; `sources` rendered as citation chips (linked); refusal + LLM-fallback states per voice doc.
- **Shell surfaces:** Landing benefit-led hero + abstract waveform motif; branded login card; dashboard first-run `EmptyState`; upload tokenized dropzone; recordings list; settings RBAC preserved exactly.
- **A11y + QA:** `eslint-plugin-jsx-a11y/recommended` enabled; custom lint guard banning `blue-*` + ad-hoc status hex; all label/control associations fixed; `aria-live` on SQI panel + chat; zero lint errors.
- **Docs:** `design-guidelines.md` updated (Brand Indigo interactive, Dark Mode in-scope); `branding/04` migration marked complete + dark mode reclassified in-scope.

### Zero regressions
- All routes compile ✅ — 10 routes generated (static + dynamic).
- Zero `blue-*` classes in components (grep clean).
- Settings RBAC role-gating logic unchanged.

---

## [2026-05-29] — Phases 1-7 Implemented

### Added
- Phase 1: Repository foundation — FastAPI backend, Next.js frontend, Docker Compose, GitHub Actions CI
- Phase 2: Backend platform — PostgreSQL schema, Alembic migrations, Google OAuth/JWT, RBAC, StorageService, AuditService, SettingsService
- Phase 3: Signal ingestion — CSV/Parquet upload (single + batch ≤50), file validation, SignalRef pattern, 8 SQI tool wrappers (vital_sqi with graceful fallback)
- Phase 4: Assessment agent pipeline — async background assessment jobs, deterministic windowed SQI + classification, smolagents ToolCallingAgent with Ollama fallback, agent log persistence
- Phase 5: Reporting & governance — automatic JSON/HTML/PDF report generation, report freshness detection, append-only segment override events (reviewer/admin RBAC), effective_classification read model
- Phase 6: Practitioner dashboard — Next.js pages (dashboard, upload, monitor, report, settings, login, chat), TanStack Query hooks, waveform viewer, segment timeline, SQI panel, override form, chatbot panel
- Phase 7: Grounded chatbot — POST /api/chat with context retrieval from persisted SQI data, conversation persistence, Ollama-grounded responses with deterministic fallback

### Tests
- Backend: 63 tests passing (pytest)
- No raw waveform arrays in LLM prompts or logs

---

## [v0.7.0] — 2026-05-29 - Phases 1-7 Complete: Full MVP Implementation

### Major Features

#### Phase 1: Repository Foundation
- Initialized monorepo with backend (FastAPI), frontend (Next.js 14), and docs
- Created reproducible Docker Compose with postgres, ollama, backend, frontend services
- Established CI/CD with GitHub Actions (lint, test, build, Docker smoke check)
- Added Makefile with development shortcuts (up, down, test, lint, migrate, seed)
- Documented project scope, local setup, testing strategy, and data privacy

**Impact:** Foundation for all subsequent phases.

#### Phase 2: Backend Platform (Auth, Database, Settings)
- Implemented SQLAlchemy 2.0 async models for all core domains
- Established Alembic migrations with schema versioning
- Added Google OAuth/JWT authentication with role-based access control (admin, researcher, reviewer, readonly)
- Implemented settings service with persistent threshold configuration and `GET/PUT /api/settings/thresholds`
- Added audit service with request ID middleware and mutation tracking
- Standardized error responses with `{error, detail, request_id}` schema

**Impact:** Secure, auditable, configurable backend foundation.

#### Phase 3: Signal Ingestion & SQI Tools (File Upload, Validation, Tool Wrappers)
- Created single and batch upload endpoints (`POST /api/recordings/upload`, `/batch-upload`)
- Implemented comprehensive file validation (format, size, path traversal, headers, channels)
- Added CSV/Parquet support for ECG and PPG signals (EDF/WFDB deferred)
- Created `SignalRef` pattern to prevent raw waveform arrays in LLM prompts
- Wrapped 8 approved vital_sqi tools with error handling and fallback
- Implemented recording retrieval endpoints (`GET /api/recordings`, `/api/recordings/{id}`)
- Added checksum verification and synthetic test fixtures

**Impact:** Safe, validated signal ingestion with approved signal processing tools.

#### Phase 4: Assessment Agent Pipeline (Background Jobs, SQI Computation, Agent Logs)
- Implemented async assessment job creation (`POST /api/assess`)
- Built deterministic windowed SQI computation with configurable segment duration
- Integrated smolagents `ToolCallingAgent` with Ollama (Qwen3-8B) LLM
- Persisted segments, SQI results, and agent logs with immutable AI classification
- Implemented rule-based fallback when LLM unavailable
- Added job status tracking (queued, processing, completed, failed, cancelled)
- Created assessment query endpoints for job status, results, logs, and segment detail

**Impact:** Automated signal quality assessment with explainable agent reasoning.

#### Phase 5: Reporting & Feedback Governance (Reports, Overrides, Freshness)
- Designed and implemented report JSON schema v1.0 (summary, timeline, recommendations, limitations)
- Automated report generation on assessment completion
- Added HTML and PDF export with WeasyPrint
- Implemented segment override API with append-only event design
- Created override supersede pattern to preserve feedback history
- Implemented report freshness detection (stale after later overrides)
- Added effective classification helper (override else AI)
- Enforced RBAC for overrides (reviewer/admin only)
- Implemented feedback/learning workflow (candidate → approval → promoted/rolled back)

**Impact:** Immutable AI outputs with reviewable feedback governance and audit trail.

#### Phase 6: Practitioner Dashboard (Frontend, Waveform Viewer, Report Viewer, Settings)
- Built Next.js 14 frontend with App Router and TypeScript
- Created API client with auth interceptors and error handling
- Implemented upload page with drag-drop, single/batch upload, validation, progress tracking
- Built waveform viewer with Recharts and segment overlay rendering
- Added segment timeline and SQI scores panel
- Implemented role-aware override panel (reviewer/admin only)
- Created report viewer with stale warning banner and export buttons
- Added settings page for threshold configuration
- Implemented agent log viewer with collapsible reasoning entries
- Built dashboard with KPI cards, alert summaries, and recent recordings
- Targeted WCAG 2.1 AA accessibility

**Pages:** `/dashboard`, `/upload`, `/recordings/[id]/monitor`, `/recordings/[id]/report`, `/settings`, `/login`

**Impact:** Intuitive clinical interface for practitioners to upload, review, and provide feedback.

#### Phase 7: Grounded Chatbot (Chat API, Message Persistence, LLM Grounding)
- Implemented chat endpoint (`POST /api/chat`) with conversation persistence
- Built grounding service that retrieves recording context (max 50 segments, no raw arrays)
- Integrated Ollama-grounded responses with deterministic fallback templates
- Created question classifier for common intents (segment reason, quality, metrics, terminology, overrides)
- Implemented constrained system prompt forbidding unsupported values
- Added message sources tracking for auditability
- Built frontend chat page (`/chat`) with recording selector and suggested questions
- Implemented chatbot panel component with markdown rendering

**Impact:** Narrow, grounded AI assistant that explains quality assessments without fabrication.

### Technology Stack

**Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Google OAuth, Ollama, vital_sqi, WeasyPrint  
**Frontend:** Next.js 14, React, TypeScript, Tailwind CSS, TanStack Query, Recharts, shadcn/ui  
**Infrastructure:** Docker Compose, PostgreSQL, Ollama, GitHub Actions  
**Testing:** pytest, Jest, integration tests with golden files  

### Metrics

- **56 Python backend files** (~8.5K LOC)
- **27 TypeScript frontend files** (~6.8K LOC)
- **63 passing tests** across unit, integration, and component tests
- **Zero hardcoded secrets** (env samples only)
- **WCAG 2.1 AA** accessibility target for dashboard

### Breaking Changes

None — first release.

### Security

- Google OAuth/JWT for all non-health endpoints
- Role-based access control (admin, researcher, reviewer, readonly)
- Append-only audit events for all mutations
- Path traversal prevention on file uploads
- No raw waveform arrays in LLM prompts or logs
- Sanitized report HTML and chatbot markdown output

### Known Limitations

- Single-channel assessment only (multi-channel post-MVP)
- CSV/Parquet file support (EDF/WFDB deferred)
- Local file storage (GCS adapter ready for cloud)
- ToolCallingAgent only (CodeAgent requires security review)
- Ollama LLM (cloud inference deferred)
- 50-segment limit in chat grounding (performance constraint)

### Deferred (Post-MVP)

- EDF and MIT-WFDB file format support
- Multi-channel ECG processing and per-channel SQI aggregation
- Cloud deployment (AWS, GCP, Azure)
- Automated model retraining from approved overrides
- Additional signal types (HRV, respiratory)
- Mobile responsive design

### Documentation

- `README.md`: Project scope, setup, local dev, testing
- `CLAUDE.md`: Developer workflows, code standards, PR requirements
- `docs/development-roadmap.md`: Phase status and progress tracking
- `docs/codebase-summary.md`: Codebase structure and module overview
- `docs/code-standards.md`: Backend/frontend conventions, error handling, security
- `docs/system-architecture.md`: System design, data model, API contracts
- `plans/*/phase-*.md`: Detailed phase documentation with implementation details

---

## [v0.6.0] — 2026-05-26 - Phase 7: Grounded Chatbot Implementation

**Added:**
- Chat endpoint with conversation persistence
- Grounding service for segment/SQI context retrieval
- LLM integration with fallback templates
- Frontend chat page and chatbot panel component

---

## [v0.5.0] — 2026-05-26 - Phase 6: Practitioner Dashboard

**Added:**
- Next.js 14 App Router with TypeScript
- Upload page with drag-drop and batch support
- Waveform viewer with Recharts
- Segment detail and override panels
- Report viewer with stale warning
- Settings configuration page
- Dashboard with KPI summary

---

## [v0.4.0] — 2026-05-26 - Phase 5: Reporting & Feedback Governance

**Added:**
- Report JSON schema v1.0
- Automatic report generation on assessment completion
- HTML/PDF export with WeasyPrint
- Segment override API with append-only design
- Report freshness detection
- Effective classification helper
- Feedback/learning workflow

---

## [v0.3.0] — 2026-05-26 - Phase 4: Assessment Agent Pipeline

**Added:**
- Async assessment job creation and background processing
- Windowed SQI computation with configurable segments
- smolagents ToolCallingAgent with Ollama LLM
- Agent log persistence with structured output
- Rule-based fallback for LLM unavailability
- Job status tracking and result endpoints

---

## [v0.2.0] — 2026-05-25 - Phase 3: Signal Ingestion & SQI Tools

**Added:**
- Single and batch upload endpoints (50 file limit)
- CSV/Parquet file format support
- File validation (format, size, headers, channels)
- Path traversal prevention
- Checksum verification
- 8 vital_sqi tool wrappers with error handling
- SignalRef pattern for safe waveform handling
- Recording retrieval endpoints

---

## [v0.1.0] — 2026-05-25 - Phase 2: Backend Platform

**Added:**
- SQLAlchemy 2.0 async models for all domains
- Alembic migrations with schema versioning
- Google OAuth/JWT authentication
- Role-based access control (admin, researcher, reviewer, readonly)
- Settings service with persistent thresholds
- Audit service with request ID middleware
- Error response standardization
- Health endpoint

---

## [v0.0.1] — 2026-05-25 - Phase 1: Repository Foundation

**Initial Release:**
- Monorepo structure with backend (FastAPI), frontend (Next.js), docs
- Docker Compose with postgres, ollama, services
- GitHub Actions CI/CD pipeline
- Makefile development shortcuts
- Documentation: README.md, CLAUDE.md
- Project scope: ECG/PPG signal quality monitoring

---

## Version Numbering

Versions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR:** Significant feature addition or breaking change (each phase)
- **MINOR:** Feature additions within phase (sub-features)
- **PATCH:** Bug fixes, documentation, minor improvements

## Upgrade Path

- v0.0.1 → v0.1.0: Requires database migration (`alembic upgrade head`)
- v0.1.0 → v0.2.0: No breaking changes; new upload endpoints
- v0.2.0 → v0.3.0: No breaking changes; new assessment jobs
- v0.3.0 → v0.4.0: No breaking changes; new report endpoints
- v0.4.0 → v0.5.0: No breaking changes; frontend-only
- v0.5.0 → v0.6.0: No breaking changes; chat endpoints
- v0.6.0 → v0.7.0: No breaking changes; stabilization and Phase 8 prep

---

## Support

For issues, questions, or contributions:
- **Documentation:** See `docs/` directory
- **Development:** See `CLAUDE.md` and `.github/`
- **Planning:** See `plans/` directory for phase details
- **Testing:** Run `make test` locally or see CI logs on GitHub Actions
