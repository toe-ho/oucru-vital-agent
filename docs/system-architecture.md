# System Architecture

**Last Updated:** 2026-05-29  
**Status:** MVP Complete (Phases 1-7)

## System Overview

OUCRU Vital Agent is a three-layer system:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 14)                        │
│           User uploads, monitors, reviews, provides feedback    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/JWT
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI/async)                        │
│  Orchestrates assessment, persists results, serves web API     │
└──────────┬──────────────────────────────────┬──────────────────┘
           │                                  │
      ┌────▼─────┐                       ┌────▼──────┐
      │ PostgreSQL│ (persistence)        │ Ollama LLM │ (optional)
      └───────────┘                      └───────────┘
           │
      ┌────▼──────────────┐
      │ Local File Storage│ (dev)
      └───────────────────┘
```

### Key Architectural Decisions

1. **Separation of Concerns**
   - Frontend: UI/UX, user interaction, form validation
   - Backend: Business logic, signal processing, audit/compliance
   - Agent: Agentic interpretation with deterministic fallback

2. **Immutability & Auditability**
   - AI classification (`segments.classification`) is write-once
   - Overrides are append-only `SegmentOverrideEvent` rows
   - All mutations logged with request IDs

3. **Privacy by Design**
   - No raw waveform arrays in LLM prompts or logs
   - Use `SignalRef` for opaque references to signals
   - Metadata and statistics only sent to agent

4. **Graceful Degradation**
   - Full assessment pipeline works without Ollama
   - Fallback to rule-based classification if LLM unavailable
   - Chat uses deterministic templates on LLM failure

5. **Single Responsibility**
   - Services are thin (100-200 LOC)
   - Each router owns one domain
   - Utilities extracted to dedicated modules

## Data Flow

### Upload Flow

```
User selects file(s)
       ↓
Frontend validates format/size
       ↓
POST /api/recordings/upload (or batch-upload)
       ↓
Backend: StorageService saves file
Backend: RecordingIngestionService parses metadata
Backend: Recording row created in DB
       ↓
Response: recording_id + status=queued
       ↓
Frontend: Redirect to /upload?recording_id=X
```

### Assessment Flow

```
User clicks "Assess" on recording
       ↓
POST /api/assess with recording_id
       ↓
Backend: AssessmentJob created (status=queued)
Backend: Background task enqueued
       ↓
Background Task:
  1. Assessment Job status → processing
  2. Load signal from disk (via SignalRef)
  3. Compute windowed SQI (vital_sqi)
  4. Create Segment rows with SQI results
  5. For each segment:
     - Call smolagents ToolCallingAgent
     - Store AI classification (immutable)
     - Log tool invocations
  6. Create Report (JSON) with findings
  7. Job status → completed
       ↓
Frontend polls GET /api/assess/{id} → sees completed
Frontend redirects to /recordings/{id}/monitor
```

### Feedback Flow

```
Reviewer views segment classification
       ↓
Reviewer disagrees with AI verdict
       ↓
POST /api/segments/{segment_id}/overrides
  {
    "classification": "reject",
    "rationale": "High motion artifact"
  }
       ↓
Backend: SegmentOverrideEvent appended (append-only)
Backend: Audit event logged
       ↓
GET /api/segments/{segment_id}/effective-classification
  → Returns override (if exists and active) or AI classification
       ↓
GET /api/reports/{report_id}/freshness
  → Returns "stale" (overrides newer than report.generated_at)
       ↓
Frontend shows stale warning, offers "Regenerate Report"
       ↓
User clicks "Regenerate"
       ↓
POST /api/reports/{id}/regenerate
  → New Report created with effective classifications
```

### Chat Flow

```
User asks: "Why was segment 3 rejected?"
       ↓
POST /api/chat
  {
    "message": "Why was segment 3 rejected?",
    "recording_id": 42
  }
       ↓
Backend: ChatGroundingService:
  1. Classify intent (e.g., "segment_reason")
  2. Retrieve segment data (no raw arrays)
  3. Build context: up to 50 segments with metadata
  4. Send to Ollama + system prompt
  5. If Ollama fails → return deterministic template
       ↓
Backend: ChatMessage created + persisted
Response: {"message": "Segment 3 was rejected because...", "sources": [...]}
       ↓
Frontend: Render markdown response + sources
```

## Database Schema (Core Tables)

### Users & Access Control

```
users
  id (PK)
  email (unique)
  google_id
  created_at

roles
  id (PK)
  name (admin, researcher, reviewer, readonly)

user_roles
  user_id (FK)
  role_id (FK)
  assigned_at
```

### Recordings & Assessment

```
recordings
  id (PK)
  filename
  format (csv/parquet)
  duration_ms
  sampling_rate
  channel_name
  signal_type (ecg/ppg)
  created_by (FK users)
  created_at

assessment_jobs
  id (PK)
  recording_id (FK recordings)
  status (queued/processing/completed/failed/cancelled)
  started_at
  completed_at
  error_message

segments
  id (PK)
  recording_id (FK recordings)
  start_ms
  end_ms
  classification (accept/reject/uncomputable) -- write-once
  confidence_score
  created_at

sqi_results
  id (PK)
  segment_id (FK segments)
  metric_name (e.g., sqi_hr_variability)
  score (0.0-1.0)
  pass (bool)

segment_override_events
  id (PK)
  segment_id (FK segments)
  overridden_by (FK users)
  classification (accept/reject/uncomputable)
  rationale (text)
  created_at
  -- No update; always append new row
```

### Reports

```
reports
  id (PK)
  recording_id (FK recordings)
  generated_by (FK users)
  generated_at
  json_data (JSON schema v1.0)
  html_content
  pdf_content
  created_at
```

### Chat & Conversations

```
conversations
  id (PK)
  recording_id (FK recordings)
  initiated_by (FK users)
  created_at

chat_messages
  id (PK)
  conversation_id (FK conversations)
  author (user/system)
  message (text)
  sources (JSON)
  created_at
```

### Audit & Logs

```
agent_logs
  id (PK)
  assessment_job_id (FK assessment_jobs)
  tool_name
  tool_input (JSON)
  tool_output (JSON)
  reasoning (text)
  created_at

audit_events
  id (PK)
  request_id (UUID)
  user_id (FK users, nullable)
  action (created/updated/deleted)
  resource_type (recording/segment/override/report)
  resource_id
  changes (JSON)
  created_at
```

### Settings

```
settings
  key (PK, string)
  value (JSON)
  updated_by (FK users)
  updated_at
```

## Agent Architecture

### Tool Registry

The `smolagents` `ToolCallingAgent` has access to 9 approved tools:

1. **`load_signal_file`** — Load metadata + stats (no raw arrays)
2. **`compute_sqi`** — Single-point SQI (vital_sqi wrapper)
3. **`compute_sqi_windowed`** — Batch computation
4. **`preprocess_ppg`** — PPG filtering
5. **`extract_hrv_features`** — Heart-rate-variability metrics
6. **`estimate_spo2`** — SpO2 from PPG
7. **`extract_ppg_dc_layer`** — DC component
8. **`check_clinical_thresholds`** — Threshold evaluation
9. **`assess_overall_quality`** — Rule-based fallback classification

### Prompts

- **Assessment system prompt:** Instructs agent to evaluate segment quality
- **Chat system prompt:** Instructs agent to answer practitioner questions using context

Both prompts explicitly forbid unsupported values (e.g., no SpO2 if PPG unavailable).

### Fallback Logic

```python
async def interpret_assessment(segments):
    try:
        response = await ollama_agent.run(...)
        return response
    except OllamaUnavailableError:
        # No LLM → use deterministic rule-based classification
        return fallback_classify(segments)
```

Assessment job **always** completes, even without LLM.

## API Contract

### Core Endpoints

#### Authentication
- `GET /api/auth/login` → Redirect to Google OAuth
- `GET /api/auth/callback?code=...` → JWT token exchange
- `GET /api/auth/me` → User profile + roles

#### Recordings
- `POST /api/recordings/upload` → Single file upload
- `POST /api/recordings/batch-upload` → Batch ≤50 files
- `GET /api/recordings` → List (paginated)
- `GET /api/recordings/{id}` → Metadata + latest job status

#### Assessment
- `POST /api/assess` → Create async job
- `GET /api/assess/{id}` → Job status
- `GET /api/assess/{id}/results` → Segments + SQI results
- `GET /api/assess/{id}/logs` → Agent logs

#### Reports
- `GET /api/reports/{id}` → JSON report
- `GET /api/reports/{id}/export/html` → HTML render
- `GET /api/reports/{id}/export/pdf` → PDF render
- `GET /api/reports/{id}/freshness` → {"status": "fresh"|"stale"}

#### Overrides
- `POST /api/segments/{id}/overrides` → Append override event
- `GET /api/segments/{id}/overrides` → Event history
- `GET /api/segments/{id}/effective-classification` → Override or AI class

#### Chat
- `POST /api/chat` → Send message
- `GET /api/chat/conversations/{id}` → Message history

#### Settings
- `GET /api/settings/thresholds` → Current SQI thresholds
- `PUT /api/settings/thresholds` → Update (admin only)

### Error Response Shape

```json
{
  "error": "ERROR_CODE",
  "detail": "Human-readable message",
  "request_id": "req-12345678"
}
```

Common codes: `VALIDATION_ERROR`, `NOT_FOUND`, `UNAUTHORIZED`, `FORBIDDEN`, `INTERNAL_ERROR`

## Frontend Architecture

### Page Hierarchy

```
/ (Home)
├── /login (Google OAuth)
├── /dashboard (KPI summary, recent uploads)
├── /upload (File upload form)
├── /recordings/[id]
│   ├── /monitor (Waveform viewer, segments, SQI, overrides)
│   └── /report (Report viewer, export)
├── /settings (Threshold config — admin only)
└── /chat (Chat interface)
```

### State Management

1. **Auth:** `AuthContext` (user, logout)
2. **Data Fetching:** TanStack Query v5 (recording, assessment, report, override, chat hooks)
3. **Component State:** React `useState` (form fields, UI toggles)

### Component Tree

```
<Layout>
  <NavBar>
  <AuthProvider>
    <QueryClientProvider>
      <Page>
        <UploadForm> / <WaveformViewer> / <ReportViewer> / etc.
```

## Security Model

### Authentication & Authorization

1. **Google OAuth 2.0** — External identity provider
2. **JWT Token** — Issued on successful login
3. **Role-Based Access Control (RBAC)**
   - `admin` — Full access + settings override
   - `researcher` — Upload, assess, view, chat
   - `reviewer` — View, override segments, regenerate reports
   - `readonly` — View, chat only

### Data Protection

1. **At Rest:** PostgreSQL encryption (TLS optional)
2. **In Transit:** HTTPS (TLS 1.2+)
3. **In Memory:** No raw waveform arrays; use SignalRef
4. **Audit Trail:** All mutations logged with request IDs

### Privacy Guarantees

- No patient-identifiable information (email, medical record, name)
- Accept only de-identified waveform files
- LLM sees metadata only (not raw arrays)
- Storage abstraction allows GCS (encrypted at rest) in production

## Deployment Architecture

### Docker Compose Services

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Frontend │  │ Backend  │  │ Postgres │  │  Ollama  │
│ Port 3k │  │ Port 8k  │  │ Port 5k  │  │ Port 11k │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
     │             │              │             │
     └─────────────┴──────────────┴─────────────┘
              Docker network
```

**Ollama** is optional (profile-based):

```bash
# Without Ollama
docker compose up -d

# With Ollama
docker compose --profile ollama up -d
```

### Environment Configuration

**Root `.env`** — shared (Docker network):
```
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
OLLAMA_PORT=11434
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...
```

**Backend `.env`** — secrets:
```
DATABASE_URL=postgresql+asyncpg://postgres:...@postgres:5432/oucru_vital
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
JWT_SECRET_KEY=...
STORAGE_ROOT=/app/storage
OLLAMA_BASE_URL=http://ollama:11434
```

**Frontend `.env.local`** — secrets:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Performance Considerations

### Signal Processing

1. **Windowed SQI:** Configurable segment duration (default 10 seconds)
2. **Async computation:** Non-blocking background tasks
3. **Caching:** Assessment results cached in DB (no re-computation)

### Database

1. **Indexing:** Foreign keys, request_id, created_at
2. **Pagination:** Recording list, message history (limit 20-50)
3. **No N+1:** Use SQLAlchemy eager loading where needed

### Frontend

1. **Lazy loading:** Pages split by route
2. **Query caching:** TanStack Query staleTime + cacheTime
3. **Image optimization:** Recharts SVG rendering (no large assets)

### Limits

1. **Batch upload:** ≤50 files per request
2. **Chat grounding:** ≤50 segments retrieved for context
3. **Report size:** Typically <500 KB (JSON + HTML)

## Scalability (Post-MVP)

1. **Horizontal:** Multiple backend instances behind load balancer
2. **Database:** Read replicas for reporting queries
3. **Storage:** Migrate from local filesystem to GCS/S3
4. **LLM:** Move from local Ollama to cloud inference (Vertex AI)
5. **Message Queue:** Add Redis for async job orchestration
6. **Caching:** Add Redis for session + API response caching

## Monitoring & Observability (Post-MVP)

1. **Logging:** Structured logs (JSON) to stdout (docker logs)
2. **Tracing:** Request ID propagation (all responses)
3. **Metrics:** Prometheus endpoints (latency, job count, errors)
4. **Alerts:** CloudWatch/Datadog for production

Current MVP logs to stdout; centralized logging to be added.

## Known Limitations

1. **Single-channel:** ECG or PPG per file (multi-channel deferred)
2. **Local LLM:** Ollama only (cloud inference deferred)
3. **File formats:** CSV/Parquet only (EDF/WFDB deferred)
4. **ToolCallingAgent:** No CodeAgent (security review required)
5. **Chat grounding:** 50-segment max (performance constraint)
6. **Storage:** Local filesystem only (GCS adapter ready)
