# Project Overview & Product Development Requirements (PDR)

**Status:** MVP Complete (Phases 1-7)  
**Last Updated:** 2026-05-29  
**Target Completion:** Phase 8 by 2026-06-05

## Problem Statement

Clinical-grade ECG and PPG signal recordings often contain quality artifacts (motion, noise, baseline drift). Manual visual inspection by experts is time-consuming and subjective. Automated quality assessment reduces clinician burden while maintaining diagnostic confidence.

## Solution Overview

OUCRU Vital Agent is an agentic system that:
1. **Ingests** de-identified waveform files (CSV/Parquet ECG/PPG)
2. **Assesses** signal quality using signal quality indices (SQI) via `vital_sqi`
3. **Classifies** segments (accept/reject/uncomputable) with agentic reasoning
4. **Reports** findings with confidence scores and recommendations
5. **Enables** feedback governance (segment overrides) with audit trail
6. **Supports** practitioner questions via grounded chatbot

## Goals

1. **Reduce assessment time** from hours to minutes for 1-hour recordings
2. **Maintain audit trail** of all quality decisions for regulatory compliance
3. **Enable reviewer feedback** without mutating original AI outputs
4. **Provide explainability** via agent reasoning and segment confidence scores
5. **Support local deployment** without cloud dependencies (for data privacy)

## Target Users

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | All; settings override; user management | Manage system, configure thresholds, audit logs |
| **Researcher** | Upload, assess, view reports, chat | Batch process recordings, analyze patterns |
| **Reviewer** | View, override segments, generate reports | Validate assessments, provide feedback |
| **Readonly** | View, chat only | Read-only access for audits or external teams |

## MVP Scope

### Feature Set

- **File Upload:** CSV and Parquet (single/batch ≤50 files)
- **Signal Types:** ECG and PPG (single-channel per file)
- **Quality Metrics:** 8 vital_sqi measures + clinical threshold checks
- **Classification:** Accept/Reject/Uncomputable per segment
- **Reporting:** JSON/HTML/PDF auto-generated on completion
- **Feedback:** Segment-level overrides (append-only) with reviewer/admin RBAC
- **Chat:** Grounded Q&A on persisted assessment data
- **Auth:** Google OAuth/JWT with role-based access control
- **Deployment:** Local Docker Compose (postgres, backend, frontend, ollama optional)

### Non-Features (Post-MVP)

- EDF/MIT-WFDB file formats
- Multi-channel ECG processing
- Cloud deployment (AWS/GCP/Azure)
- Automated model retraining
- Mobile-responsive design
- Real-time streaming ingestion

## Architecture Principles

### 1. Privacy & Security
- Google OAuth/JWT for all endpoints (except health)
- Role-based access control (admin, researcher, reviewer, readonly)
- No raw waveform arrays in LLM prompts or logs
- Append-only audit events for all mutations
- Path traversal prevention on uploads

### 2. Immutability & Auditability
- `segments.classification` is write-once (AI output)
- Overrides are append-only SegmentOverrideEvent rows
- `effective_classification` derived at read time
- Report freshness detection (stale if overrides postdate generation)
- Request ID middleware on all responses

### 3. Graceful Degradation
- LLM failure falls back to deterministic rule-based classification
- Assessment job completes even if Ollama unavailable
- SignalRef pattern prevents raw data in agent prompts
- No signal processing dependency on LLM

### 4. Developer Experience
- Single-command Docker Compose startup
- TypeScript/React frontend with TanStack Query
- FastAPI with async SQLAlchemy
- Makefile shortcuts for common tasks
- Code under 200 LOC per file (modular design)

## Data Model Summary

### Core Entities

- **User:** Identity + role (from Google OAuth)
- **Recording:** Metadata (format, duration, sampling_rate, filename)
- **AssessmentJob:** Status (queued/processing/completed/failed), timestamps
- **Segment:** Time window [start_ms, end_ms], immutable AI classification
- **SqiResult:** Individual metric (sqi_hr_variability, etc.) + score
- **SegmentOverrideEvent:** Append-only (timestamp, reviewer, rationale, classification)
- **Report:** JSON schema v1.0 (summary, timeline, recommendations, limitations)
- **Conversation:** Message history with sources + grounding refs
- **AuditEvent:** All mutations (user, action, resource, request_id)

## API Contract (Essential Endpoints)

### Authentication
- `GET /api/auth/login` — Redirect to Google OAuth
- `GET /api/auth/callback?code=...` — Exchange code for JWT
- `GET /api/auth/me` — User profile

### Recordings
- `POST /api/recordings/upload` — Single file upload
- `POST /api/recordings/batch-upload` — Batch ≤50 files
- `GET /api/recordings` — List (paginated)
- `GET /api/recordings/{id}` — Metadata + status

### Assessment
- `POST /api/assess` — Create async job
- `GET /api/assess/{id}` — Job status
- `GET /api/assess/{id}/results` — Segments + SQI
- `GET /api/assess/{id}/logs` — Agent reasoning

### Reports
- `GET /api/reports/{id}` — JSON report
- `GET /api/reports/{id}/export/html` — HTML render
- `GET /api/reports/{id}/export/pdf` — PDF render
- `GET /api/reports/{id}/freshness` — Stale/fresh status

### Overrides (Reviewer/Admin)
- `POST /api/segments/{id}/overrides` — Append event
- `GET /api/segments/{id}/overrides` — Event history
- `GET /api/segments/{id}/effective-classification` — Override or AI class

### Chat
- `POST /api/chat` — Send message (retrieves context)
- `GET /api/chat/conversations/{id}` — Message history

### Settings (Admin)
- `GET /api/settings/thresholds` — Current SQI thresholds
- `PUT /api/settings/thresholds` — Update (admin only)

## Success Metrics (Acceptance Criteria)

| AC | Criterion | Status |
|----|-----------|--------|
| AC-001 | Upload → assessment → report with zero manual steps | ✓ Complete |
| AC-002 | 1-hour recording assessed < 10 minutes | ⏳ Phase 8 |
| AC-003 | Dashboard load < 3 seconds | ⏳ Phase 8 |
| AC-004 | Report has all required sections (timeline, metrics, flags, recommendations) | ✓ Complete |
| AC-005 | 100% of tool invocations logged | ✓ Complete |
| AC-006 | Override feedback immutable (append-only audit) | ✓ Complete |
| AC-007 | Chat accuracy on test QA set ≥ 80% | ⏳ Phase 8 |
| AC-008 | 63+ automated tests passing | ✓ Complete |
| AC-009 | Zero hardcoded secrets in codebase | ✓ Complete |
| AC-010–021 | Full acceptance criteria suite | ⏳ Phase 8 |

## Regulatory & Compliance

- **Data Privacy:** GDPR-ready (local storage, no patient PII)
- **Audit Trail:** All mutations logged with request IDs
- **Role-Based Access:** Admin/researcher/reviewer/readonly
- **Signal Handling:** No raw waveforms in logs or LLM prompts
- **Override Governance:** Append-only events with rationale tracking

## Technical Constraints

1. **Signal Processing:** vital_sqi library for all SQI computation
2. **Agent:** smolagents ToolCallingAgent (CodeAgent deferred)
3. **Storage:** Local filesystem (dev) with GCS adapter ready
4. **LLM:** Ollama + Qwen3-8B (cloud inference post-MVP)
5. **File Formats:** CSV, Parquet (single-channel; multi-channel deferred)
6. **Segment Duration:** Configurable (default 10 seconds)
7. **Batch Size:** Upload ≤50 files per request
8. **Chat Grounding:** Max 50 segments per query (performance)

## Phase Delivery

| Phase | Goal | Status | Target Date |
|-------|------|--------|-------------|
| 1 | Repository foundation | ✓ | 2026-05-29 |
| 2 | Backend platform (auth, DB, storage) | ✓ | 2026-05-29 |
| 3 | Signal ingestion & SQI tools | ✓ | 2026-05-29 |
| 4 | Assessment agent pipeline | ✓ | 2026-05-29 |
| 5 | Reporting & feedback governance | ✓ | 2026-05-29 |
| 6 | Practitioner dashboard | ✓ | 2026-05-29 |
| 7 | Grounded chatbot | ✓ | 2026-05-29 |
| 8 | Verification & demo | ⏳ | 2026-06-05 |

## Known Limitations

- Single-channel assessment only
- CSV/Parquet only (EDF/WFDB deferred)
- Local LLM only (Ollama)
- ToolCallingAgent only (CodeAgent deferred)
- 50-segment limit in chat grounding

## Success Definition

MVP is successful when:
1. All 7 phases delivered
2. 63+ tests passing
3. Acceptance criteria AC-001 through AC-010 verified
4. Demo on sample OUCRU recordings (5-10 anonymized files)
5. Deployment guide complete
6. Team review passed
