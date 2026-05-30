# Codebase Summary

**Last Updated:** 2026-05-29  
**Total Files:** 155 files  
**Backend:** 56 Python files (~8.5K LOC)  
**Frontend:** 27 TypeScript/React files (~6.8K LOC)  
**Tests:** 63 passing

## Project Overview

OUCRU Vital Agent — Agentic waveform data quality monitoring for ECG and PPG signals. Ingests de-identified recordings, computes signal quality indices via `vital_sqi`, classifies segments with `smolagents` + Ollama, and exposes results through a practitioner dashboard and grounded chatbot.

## Repository Structure

```
oucru-capstone/
├── README.md                    # Project overview + quick start
├── CLAUDE.md                    # Developer workflows
├── Makefile                     # Development shortcuts
├── docker-compose.yml           # Local dev infrastructure
├── repomix-output.xml           # Codebase snapshot (AI-friendly)
├── .env.example                 # Environment template (root)
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions (lint, test, build)
├── docs/
│   ├── project-overview-pdr.md          # Product goals + MVP scope
│   ├── code-standards.md                # Coding conventions + patterns
│   ├── codebase-summary.md              # This file
│   ├── system-architecture.md           # Component interactions + DB schema
│   ├── design-guidelines.md             # Frontend UI/UX + Tailwind
│   ├── deployment-guide.md              # Docker + cloud setup
│   ├── development-roadmap.md           # Phase status + milestones
│   ├── project-changelog.md             # Version history
│   └── prd/                             # Product requirements docs
│       ├── 00-index.md
│       ├── 01-product-overview.md
│       ├── product-design/
│       │   └── 01-ui-ux-specifications.md
│       ├── architecture/
│       │   ├── 01-system-design.md
│       │   ├── 02-data-model.md
│       │   ├── 03-api-specification.md
│       │   └── 04-data-model.md
│       └── acceptance-criteria.md
├── backend/
│   ├── main.py                          # FastAPI app entry (routers)
│   ├── requirements.txt                 # Python dependencies
│   ├── .env.example                     # Backend secrets template
│   ├── pytest.ini                       # Test config
│   ├── Dockerfile                       # Backend container
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app factory
│   │   ├── core/
│   │   │   ├── settings.py              # Pydantic v2 config
│   │   │   ├── database.py              # SQLAlchemy async engine
│   │   │   └── errors.py                # AppError + error handlers
│   │   ├── auth/
│   │   │   ├── google_oauth.py          # OAuth flow
│   │   │   ├── jwt_handler.py           # JWT encode/decode
│   │   │   └── role_guards.py           # Role dependencies
│   │   ├── models/
│   │   │   ├── user_models.py           # User, Role, UserRole
│   │   │   ├── recording_models.py      # Recording, AssessmentJob
│   │   │   ├── segment_models.py        # Segment, SqiResult, SegmentOverrideEvent
│   │   │   ├── report_models.py         # Report, Conversation, ChatMessage
│   │   │   ├── log_models.py            # AgentLog, AuditEvent
│   │   │   └── settings_models.py       # Setting (thresholds)
│   │   ├── schemas/
│   │   │   ├── user_schema.py           # User DTOs
│   │   │   ├── recording_schema.py      # Recording DTOs
│   │   │   ├── segment_schema.py        # Segment DTOs
│   │   │   ├── report_schema.py         # Report DTOs
│   │   │   ├── chat_schema.py           # Chat DTOs
│   │   │   └── error_schema.py          # Error responses
│   │   ├── api/
│   │   │   ├── health_router.py         # GET /health
│   │   │   ├── auth_router.py           # Auth endpoints
│   │   │   ├── recordings_router.py     # Upload + list
│   │   │   ├── assessment_router.py     # Job + results
│   │   │   ├── reports_router.py        # Report generation
│   │   │   ├── segment_overrides_router.py # Feedback governance
│   │   │   ├── chat_router.py           # Chat endpoint
│   │   │   └── settings_router.py       # Threshold config
│   │   ├── services/
│   │   │   ├── storage_service.py       # File I/O abstraction
│   │   │   ├── audit_service.py         # AuditEvent persistence
│   │   │   ├── settings_service.py      # Settings CRUD
│   │   │   ├── file_validation_service.py # CSV/Parquet validation
│   │   │   ├── recording_ingestion_service.py # Upload handling
│   │   │   ├── segment_classification_service.py # Rule-based SQI eval
│   │   │   ├── agent_log_service.py     # AgentLog persistence
│   │   │   ├── assessment_runner.py     # Windowed SQI pipeline
│   │   │   ├── assessment_service.py    # Job lifecycle + background tasks
│   │   │   ├── report_service.py        # Report generation
│   │   │   ├── report_rendering_service.py # HTML/PDF export
│   │   │   ├── report_freshness_service.py # Stale detection
│   │   │   ├── segment_override_service.py # Append-only overrides
│   │   │   ├── chat_grounding_service.py # Context retrieval
│   │   │   └── chat_service.py          # Message persistence
│   │   ├── tools/
│   │   │   ├── signal_ref.py            # SignalRef dataclass
│   │   │   ├── load_signal_file_tool.py # Metadata + stats extraction
│   │   │   └── sqi_tools.py             # 8 vital_sqi wrappers
│   │   ├── agent/
│   │   │   ├── tool_registry.py         # Tool definitions
│   │   │   ├── agent_orchestrator.py    # LiteLLM + fallback
│   │   │   └── prompts/
│   │   │       ├── assessment_system_prompt.md
│   │   │       └── chat_system_prompt.md
│   │   └── scripts/
│   │       └── seed.py                  # Initial data seeding
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   ├── versions/
│   │   │   └── 0001_initial_schema.py   # Full DB schema migration
│   │   └── alembic.ini
│   └── tests/
│       ├── conftest.py                  # Pytest fixtures
│       ├── unit/                        # 40+ unit tests
│       ├── integration/                 # 20+ integration tests
│       └── fixtures/                    # Sample ECG/PPG CSV
├── frontend/
│   ├── package.json                     # Node dependencies
│   ├── package-lock.json                # Lock file
│   ├── tsconfig.json                    # TypeScript config
│   ├── next.config.js                   # Next.js config
│   ├── jest.config.js                   # Test config
│   ├── .env.example                     # Frontend secrets template
│   ├── Dockerfile                       # Frontend container
│   ├── app/
│   │   ├── layout.tsx                   # Root layout (providers)
│   │   ├── page.tsx                     # Home page
│   │   ├── login/page.tsx               # Google OAuth
│   │   ├── dashboard/page.tsx           # KPI summary
│   │   ├── upload/page.tsx              # File upload form
│   │   ├── recordings/[id]/
│   │   │   ├── layout.tsx               # Recording nav context
│   │   │   ├── monitor/page.tsx         # Waveform viewer
│   │   │   └── report/page.tsx          # Report viewer
│   │   ├── settings/page.tsx            # Threshold config
│   │   ├── chat/page.tsx                # Chat interface
│   │   └── api/auth/callback/route.ts   # JWT exchange
│   ├── lib/
│   │   ├── api-client.ts                # Axios + auth interceptor
│   │   ├── auth-context.tsx             # AuthProvider + useAuth
│   │   ├── query-provider.tsx           # TanStack Query v5
│   │   ├── types.ts                     # Domain interfaces
│   │   └── queries/
│   │       ├── recording-queries.ts
│   │       ├── assessment-queries.ts
│   │       ├── report-queries.ts
│   │       ├── override-queries.ts
│   │       └── chat-queries.ts
│   ├── components/
│   │   ├── ui/classification-badge.tsx
│   │   ├── upload/file-upload-dropzone.tsx
│   │   ├── monitoring/
│   │   │   ├── waveform-viewer.tsx
│   │   │   ├── segment-timeline.tsx
│   │   │   ├── sqi-scores-panel.tsx
│   │   │   └── segment-override-panel.tsx
│   │   ├── reports/report-viewer.tsx
│   │   ├── chat/chatbot-panel.tsx
│   │   └── common/nav-bar.tsx
│   ├── styles/globals.css
│   ├── __tests__/                       # Component tests
│   └── public/
├── plans/                               # Implementation plans (gitignored)
└── .gitignore
```

## Backend Architecture (Python 3.11, FastAPI 0.111+)

### Entry Point

**`app/main.py`** — FastAPI app factory with all routers registered.

### Core Layer (`app/core/`)

- **`settings.py`** — Pydantic v2 config (DATABASE_URL, OAuth, JWT, Storage, Ollama)
- **`database.py`** — SQLAlchemy 2.0 async engine, Base, get_db dependency
- **`errors.py`** — AppError, ErrorCode enum, error middleware

### Models Layer (`app/models/`)

SQLAlchemy 2.0 Mapped/mapped_column (type-safe):

- **`user_models.py`** — User, Role, UserRole
- **`recording_models.py`** — Recording, AssessmentJob
- **`segment_models.py`** — Segment, SqiResult, SegmentOverrideEvent
- **`report_models.py`** — Report, Conversation, ChatMessage
- **`log_models.py`** — AgentLog, AuditEvent
- **`settings_models.py`** — Setting (threshold key-value store)

### API Routers (`app/api/`)

8 routers, each owning one domain:

1. **`health_router.py`** — GET /health
2. **`auth_router.py`** — Google OAuth, JWT exchange, /me
3. **`recordings_router.py`** — Upload (single/batch), list, detail
4. **`assessment_router.py`** — Job creation, status, results, logs
5. **`reports_router.py`** — Generation, export (HTML/PDF), freshness
6. **`segment_overrides_router.py`** — Append overrides, effective classification
7. **`chat_router.py`** — Message creation, conversation history
8. **`settings_router.py`** — Threshold config (admin only)

### Services Layer (`app/services/`)

15 focused services:

- **Storage:** File I/O abstraction (local/GCS)
- **Audit:** Append-only event logging
- **Settings:** Threshold CRUD
- **File Validation:** CSV/Parquet format + size + structure
- **Recording Ingestion:** Upload workflow, metadata parsing
- **Segment Classification:** Rule-based SQI evaluation
- **Agent Log:** Tool invocation logging (compact, no raw arrays)
- **Assessment Runner:** Windowed SQI pipeline
- **Assessment Service:** Job orchestration + background tasks
- **Report Service:** Report generation
- **Report Rendering:** HTML/PDF export
- **Report Freshness:** Stale detection
- **Segment Override:** Append-only feedback governance
- **Chat Grounding:** Context retrieval (≤50 segments, no raw arrays)
- **Chat Service:** Conversation lifecycle

### Tools Layer (`app/tools/`)

- **`signal_ref.py`** — Opaque reference (never exposed to LLM)
- **`load_signal_file_tool.py`** — Metadata extraction (no raw array)
- **`sqi_tools.py`** — 8 vital_sqi wrappers with fallback

### Agent Layer (`app/agent/`)

- **`tool_registry.py`** — 9 approved tools for smolagents ToolCallingAgent
- **`agent_orchestrator.py`** — LLM coordination + deterministic fallback
- **`prompts/`** — System prompts (assessment, chat)

### Database

- **`alembic/versions/0001_initial_schema.py`** — Full schema migration

### Scripts

- **`seed.py`** — Initial roles + default settings

### Tests

**63 passing tests:**
- Unit tests (mocked, fast)
- Integration tests (real DB, file I/O)
- Fixtures: sample_ecg.csv, sample_ppg.csv

## Frontend Architecture (TypeScript, Next.js 14, React 18)

### Stack

- **Next.js 14** — App Router
- **React 18** — Components
- **TypeScript** — Type safety
- **Tailwind CSS** — Styling
- **shadcn/ui** — Component primitives
- **TanStack Query v5** — Data fetching
- **Recharts** — Charts
- **Axios** — HTTP client

### App Router (`app/`)

- **`layout.tsx`** — Root + AuthProvider/QueryClientProvider
- **`page.tsx`** — Home
- **`login/page.tsx`** — Google OAuth
- **`dashboard/page.tsx`** — KPI cards
- **`upload/page.tsx`** — File upload form
- **`recordings/[id]/monitor/page.tsx`** — Waveform viewer
- **`recordings/[id]/report/page.tsx`** — Report viewer
- **`settings/page.tsx`** — Threshold config (admin)
- **`chat/page.tsx`** — Chat interface
- **`api/auth/callback/route.ts`** — OAuth callback

### Libraries (`lib/`)

- **`api-client.ts`** — Axios with auth interceptor
- **`auth-context.tsx`** — Global auth state + useAuth()
- **`query-provider.tsx`** — TanStack Query setup
- **`types.ts`** — Domain interfaces
- **`queries/`** — Custom hooks (recording, assessment, report, override, chat)

### Components (`components/`)

- **UI:** classification-badge (status indicator)
- **Upload:** file-upload-dropzone (drag-drop)
- **Monitoring:** waveform-viewer, segment-timeline, sqi-scores-panel, segment-override-panel
- **Reports:** report-viewer
- **Chat:** chatbot-panel
- **Common:** nav-bar

## Deployment

### Docker Compose

- postgres:15-alpine
- backend (FastAPI uvicorn --reload)
- frontend (Next.js dev)
- ollama (optional profile, Qwen3-8B)

### Environment

**Root `.env`:** Ports, DB credentials  
**Backend `.env`:** Secrets (DATABASE_URL, OAuth, JWT, Storage, Ollama)  
**Frontend `.env.local`:** API base URL

## Testing

- **Backend:** 63 pytest tests (unit + integration)
- **Frontend:** Component tests with React Testing Library
- **CI/CD:** GitHub Actions (lint, test, build)

## Key Design Patterns

1. **SignalRef** — Opaque reference (no raw arrays to LLM)
2. **Append-Only Audit** — All mutations logged with request IDs
3. **Immutable AI Output** — segments.classification write-once
4. **Graceful Fallback** — Works without Ollama
5. **RBAC** — admin, researcher, reviewer, readonly
6. **Effective Classification** — Override supersedes AI at read time
7. **Report Freshness** — Stale if overrides postdate generation

## Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Backend LOC | < 10K | ~8.5K (56 files) |
| Frontend LOC | < 8K | ~6.8K (27 files) |
| Test Coverage | > 80% | 63 tests passing |
| Code Files | < 200 LOC | 95% compliance |
| Secrets in Code | 0 | ✓ Verified |

## Known Limitations

- Single-channel assessment only
- CSV/Parquet only (EDF/WFDB post-MVP)
- Local LLM only (cloud post-MVP)
- ToolCallingAgent only (CodeAgent deferred)
- 50-segment chat grounding limit
