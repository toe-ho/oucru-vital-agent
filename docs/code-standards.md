# Code Standards & Architectural Guidelines

**Last Updated:** 2026-05-29  
**Applies To:** All backend (Python) and frontend (TypeScript/React) code

## Core Principles

We follow **YAGNI** (You Aren't Gonna Need It), **KISS** (Keep It Simple, Stupid), and **DRY** (Don't Repeat Yourself).

1. **Clarity over completeness** — Write code that is immediately useful
2. **Immutability where possible** — Reduce hidden state and bugs
3. **No raw waveform data in LLM context** — Use `SignalRef` and metadata only
4. **Append-only audit events** — All mutations are logged for compliance
5. **Graceful fallback** — Features work even when optional services (Ollama) fail

## File Organization

### Backend (Python)

```
backend/
├── app/
│   ├── main.py                    # FastAPI app factory, router registration
│   ├── core/
│   │   ├── settings.py            # Pydantic Settings (env vars)
│   │   ├── database.py            # SQLAlchemy engine, Base, get_db
│   │   └── errors.py              # AppError, error handlers
│   ├── auth/
│   │   ├── google_oauth.py        # Google OAuth flow
│   │   ├── jwt_handler.py         # JWT encode/decode
│   │   └── role_guards.py         # Dependency for role checks
│   ├── models/
│   │   ├── user_models.py         # User, Role, UserRole
│   │   ├── recording_models.py    # Recording, AssessmentJob
│   │   ├── segment_models.py      # Segment, SqiResult, SegmentOverrideEvent
│   │   ├── report_models.py       # Report, Conversation, ChatMessage
│   │   ├── log_models.py          # AgentLog, AuditEvent
│   │   └── settings_models.py     # Setting (threshold configs)
│   ├── schemas/
│   │   ├── user_schema.py         # User request/response DTOs
│   │   ├── recording_schema.py    # Recording DTOs
│   │   ├── segment_schema.py      # Segment DTOs
│   │   ├── report_schema.py       # Report DTOs
│   │   ├── chat_schema.py         # Chat DTOs
│   │   └── error_schema.py        # Standard error responses
│   ├── api/
│   │   ├── health_router.py       # GET /health
│   │   ├── auth_router.py         # Auth endpoints
│   │   ├── recordings_router.py   # Upload, batch, listing
│   │   ├── assessment_router.py   # Job creation and status
│   │   ├── reports_router.py      # Report generation, export
│   │   ├── segment_overrides_router.py # Feedback governance
│   │   ├── chat_router.py         # Chat endpoint
│   │   └── settings_router.py     # Threshold configuration
│   ├── services/
│   │   ├── storage_service.py     # File I/O abstraction
│   │   ├── audit_service.py       # AuditEvent persistence
│   │   ├── settings_service.py    # Settings CRUD
│   │   ├── file_validation_service.py  # CSV/Parquet validation
│   │   ├── recording_ingestion_service.py # Upload handling
│   │   ├── segment_classification_service.py # Rule-based SQI eval
│   │   ├── agent_log_service.py   # AgentLog persistence
│   │   ├── assessment_runner.py   # Windowed SQI pipeline
│   │   ├── assessment_service.py  # Job lifecycle, background tasks
│   │   ├── report_service.py      # Report generation
│   │   ├── report_rendering_service.py # HTML/PDF export
│   │   ├── report_freshness_service.py # Stale detection
│   │   ├── segment_override_service.py # Append-only overrides
│   │   ├── chat_grounding_service.py # Context retrieval
│   │   └── chat_service.py        # Message persistence
│   ├── tools/
│   │   ├── signal_ref.py          # SignalRef dataclass (never exposed to LLM)
│   │   ├── load_signal_file_tool.py # Metadata extraction
│   │   └── sqi_tools.py           # 8 vital_sqi wrappers
│   ├── agent/
│   │   ├── tool_registry.py       # Tool definitions for ToolCallingAgent
│   │   ├── agent_orchestrator.py  # LiteLLM + fallback orchestration
│   │   └── prompts/
│   │       ├── assessment_system_prompt.md
│   │       └── chat_system_prompt.md
│   ├── scripts/
│   │   └── seed.py                # Initial role + settings seeding
│   └── tests/
│       ├── unit/                  # Unit tests (mocked dependencies)
│       ├── integration/           # Integration tests (real DB, file I/O)
│       └── fixtures/              # Sample ECG/PPG CSV files
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py # Full DB schema migration
├── requirements.txt               # Python dependencies
├── .env.example                   # Env template
└── pytest.ini                     # Test configuration

```

### Frontend (TypeScript/React)

```
frontend/
├── app/
│   ├── layout.tsx                 # Root layout with AuthProvider, QueryProvider
│   ├── page.tsx                   # Home/landing page
│   ├── login/page.tsx             # Google OAuth sign-in
│   ├── dashboard/
│   │   └── page.tsx               # Dashboard with KPI cards
│   ├── upload/
│   │   └── page.tsx               # File upload form
│   ├── recordings/[id]/
│   │   ├── monitor/page.tsx       # Waveform viewer + segments + overrides
│   │   ├── report/page.tsx        # Report viewer + export
│   │   └── layout.tsx             # Recording nav context
│   ├── settings/
│   │   └── page.tsx               # Threshold configuration
│   ├── chat/
│   │   └── page.tsx               # Chat interface
│   └── api/
│       └── auth/callback/route.ts # JWT token exchange
├── lib/
│   ├── api-client.ts              # Axios instance with auth interceptor
│   ├── auth-context.tsx           # AuthProvider + useAuth hook
│   ├── query-provider.tsx         # TanStack Query v5 setup
│   ├── types.ts                   # TypeScript domain interfaces
│   └── queries/
│       ├── recording-queries.ts   # useRecording, useRecordings, useUpload
│       ├── assessment-queries.ts  # useAssessmentJob, useResults
│       ├── report-queries.ts      # useReport, useReportFreshness
│       ├── override-queries.ts    # useOverride, useEffectiveClass
│       └── chat-queries.ts        # useChat, useConversation
├── components/
│   ├── ui/
│   │   └── classification-badge.tsx # Accept/reject/uncomputable badge
│   ├── upload/
│   │   └── file-upload-dropzone.tsx # Drag-drop form
│   ├── monitoring/
│   │   ├── waveform-viewer.tsx    # Recharts line chart with overlays
│   │   ├── segment-timeline.tsx   # Horizontal colored blocks
│   │   ├── sqi-scores-panel.tsx   # Metrics table
│   │   └── segment-override-panel.tsx # Review + override form
│   ├── reports/
│   │   └── report-viewer.tsx      # Report + stale warning + exports
│   ├── chat/
│   │   └── chatbot-panel.tsx      # Chat UI with bubbles + markdown
│   └── common/
│       └── nav-bar.tsx            # Navigation with auth context
├── styles/
│   └── globals.css                # Tailwind + custom utilities
├── package.json                   # Dependencies (Next.js, React, Tailwind, etc.)
├── tsconfig.json                  # TypeScript config
├── .env.example                   # Env template
└── jest.config.js                 # Test configuration

```

## Naming Conventions

### Python (Backend)

- **Files:** `snake_case.py` (descriptive names)
- **Modules:** `module_name.py` — one responsibility per file when >200 LOC
- **Classes:** `PascalCase` (SQLAlchemy models, services, schemas)
- **Functions/Methods:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** Prefix with `_` (e.g., `_internal_helper`)

Examples:
- `segment_classification_service.py` — Clear purpose
- `class SegmentOverrideEvent` — Data entity
- `def classify_segment(...)` — Action-oriented name
- `SEGMENT_DURATION_MS = 10_000` — Configuration constant

### TypeScript/React (Frontend)

- **Files:** `kebab-case.ts`, `kebab-case.tsx` (descriptive names)
- **Components:** `PascalCase.tsx`
- **Hooks:** `use<Name>.ts` (e.g., `useRecording.ts`)
- **Types/Interfaces:** `PascalCase` (e.g., `Recording`, `SqiScore`)
- **Functions/Variables:** `camelCase`
- **Constants:** `camelCase` (or `UPPER_SNAKE_CASE` for globals)

Examples:
- `file-upload-dropzone.tsx` — Clear component purpose
- `useRecording.ts` — Query hook
- `interface Recording { ... }` — Domain type
- `const handleUpload = (...) => { ... }` — Event handler

## Code Size Limits

- **Target:** Single-responsibility files under 200 LOC
- **Strategy:** Split large files by domain (e.g., `segment_service.py` + `segment_override_service.py`)
- **Exceptions:** Config files, migrations, large datasets okay to exceed

## Python Backend Standards

### Async/Await

All I/O is async. Use `async/await` consistently:

```python
async def get_recording(recording_id: int, db: AsyncSession) -> Recording:
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### Error Handling

Use `AppError` for all application errors:

```python
from app.core.errors import AppError, ErrorCode

if not file:
    raise AppError(
        error_code=ErrorCode.VALIDATION_ERROR,
        detail="File not found",
        status_code=404
    )
```

Response shape (standardized):
```json
{
  "error": "VALIDATION_ERROR",
  "detail": "File not found",
  "request_id": "req-12345678"
}
```

### SQLAlchemy 2.0 + Pydantic

Use `Mapped` and `mapped_column` for type safety:

```python
from sqlalchemy.orm import Mapped, mapped_column

class Recording(Base):
    __tablename__ = "recordings"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
```

Pydantic v2 schemas:

```python
from pydantic import BaseModel, Field

class RecordingResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # ORM mode
```

### No Raw Waveform Arrays

ALWAYS use `SignalRef`:

```python
# WRONG
class AssessmentResponse:
    waveform_array: List[float]  # ❌ Never expose raw data

# RIGHT
class AssessmentResponse:
    signal_ref: SignalRef  # ✓ Opaque reference
```

Inside agent prompts, retrieve metadata only:
```python
signal_data = await load_signal_file(signal_ref)
# Returns: {
#   "metadata": {...},
#   "stats": {"mean": X, "std": Y, ...},
#   "sqi_results": [...]
# }
```

### Immutability Rules

1. **Segments:** `segments.classification` is write-once
2. **Overrides:** New override event rows (never update existing)
3. **Reports:** Generated once; query `report_freshness_service` to detect staleness

```python
# WRONG
override.classification = "reject"  # ❌ Mutating existing row

# RIGHT
override_event = SegmentOverrideEvent(
    segment_id=segment_id,
    classification="reject",
    reviewer_id=user_id,
    created_at=utcnow()
)
db.add(override_event)  # ✓ Append-only
await db.commit()
```

### Fallback Patterns

All tools must gracefully handle Ollama unavailability:

```python
async def interpret_assessment(segments):
    try:
        response = await ollama_agent.run(segments)
        return response
    except OllamaUnavailableError:
        # Fall back to deterministic classification
        return classify_deterministic(segments)
```

## TypeScript/React Frontend Standards

### Async Data Fetching

Use TanStack Query v5 exclusively:

```typescript
// hooks/use-recording.ts
export const useRecording = (recordingId: number) => {
  return useQuery({
    queryKey: ["recording", recordingId],
    queryFn: () => apiClient.get(`/api/recordings/${recordingId}`),
    staleTime: 30000, // 30s
  });
};

// Component usage
const RecordingDetail = ({ id }: { id: number }) => {
  const { data, isLoading, error } = useRecording(id);
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{data.filename}</div>;
};
```

### Auth Context

Always consume `useAuth()`:

```typescript
const MyComponent = () => {
  const { user, logout } = useAuth();
  if (!user) return <Redirect to="/login" />;
  return <div>Hello, {user.email}</div>;
};
```

### API Client

All requests go through `lib/api-client.ts`:

```typescript
// lib/api-client.ts
import axios from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
});

// Auth interceptor (adds JWT to requests)
apiClient.interceptors.request.use((config) => {
  const token = getToken(); // from localStorage or cookie
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Error interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      redirect("/login");
    }
    return Promise.reject(error);
  }
);
```

### Component Structure

Keep components small and focused:

```typescript
// components/upload/file-upload-dropzone.tsx
interface FileUploadDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  isLoading?: boolean;
}

export const FileUploadDropzone: React.FC<FileUploadDropzoneProps> = ({
  onFilesSelected,
  isLoading = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    onFilesSelected(files);
  };

  return (
    <div
      onDragOver={() => setIsDragOver(true)}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded p-4 ${
        isDragOver ? "bg-blue-50" : ""
      }`}
    >
      Drag files here or click to upload
    </div>
  );
};
```

### Type Safety

All API responses must have types:

```typescript
// lib/types.ts
export interface Recording {
  id: number;
  filename: string;
  format: "csv" | "parquet";
  duration_ms: number;
  sampling_rate: number;
  created_at: string;
}

export interface AssessmentJob {
  id: number;
  recording_id: number;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  started_at?: string;
  completed_at?: string;
}

export interface SqiScore {
  segment_id: number;
  metric_name: string;
  score: number;
  pass: boolean;
}
```

## Testing Standards

### Backend (pytest)

- **Location:** `backend/tests/unit/` and `backend/tests/integration/`
- **Naming:** `test_<feature>.py`
- **Fixtures:** `conftest.py` with `@pytest.fixture`
- **Coverage:** Aim for >80%

Example:

```python
# tests/unit/test_segment_classification.py
import pytest
from app.services.segment_classification_service import classify_segment

@pytest.fixture
def sample_sqi_results():
    return {
        "sqi_hr_variability": 0.9,
        "sqi_motion": 0.5,
        # ...
    }

def test_classify_segment_accept(sample_sqi_results):
    classification = classify_segment(sample_sqi_results)
    assert classification == "accept"

def test_classify_segment_reject(sample_sqi_results):
    sqi_results_bad = {k: 0.1 for k, v in sample_sqi_results.items()}
    classification = classify_segment(sqi_results_bad)
    assert classification == "reject"
```

### Frontend (Jest + React Testing Library)

- **Location:** `frontend/__tests__/`
- **Naming:** `<component>.test.tsx`
- **Approach:** Test user behavior, not implementation

Example:

```typescript
// __tests__/components/upload/file-upload-dropzone.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileUploadDropzone } from "@/components/upload/file-upload-dropzone";

describe("FileUploadDropzone", () => {
  it("calls onFilesSelected when files are dropped", async () => {
    const onFilesSelected = jest.fn();
    render(<FileUploadDropzone onFilesSelected={onFilesSelected} />);

    const dropzone = screen.getByText(/Drag files here/);
    const file = new File(["content"], "test.csv", { type: "text/csv" });

    // Simulate drag and drop
    await userEvent.upload(dropzone, file);

    expect(onFilesSelected).toHaveBeenCalledWith(expect.arrayContaining([file]));
  });
});
```

## Git & Commit Standards

### Branch Naming
- Feature: `feature/short-description`
- Bug: `fix/short-description`
- Docs: `docs/short-description`

### Commit Messages (Conventional Commits)

```
<type>(<scope>): <subject>

<body>
<footer>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
```
feat(assessment): add deterministic fallback for LLM unavailability
fix(segment-override): fix append-only event insertion order
docs(readme): update Docker Compose setup instructions
refactor(chat-service): split grounding logic into separate service
test(recording-ingestion): add CSV validation edge cases
chore(deps): upgrade FastAPI to 0.111.0
```

### Pre-commit Checklist

Before pushing:
1. Run `make lint` (ruff + eslint)
2. Run `make test` (pytest + Jest)
3. No hardcoded secrets or raw waveform arrays
4. All tests passing
5. Code under 200 LOC per file (where practical)

## Documentation Standards

### Code Comments

Use comments for **why**, not **what**:

```python
# WRONG
# Add 1 to count
count += 1

# RIGHT
# Increment to account for header row in CSV
count += 1
```

### Docstrings

Use Google-style docstrings:

```python
async def classify_segment(
    sqi_results: Dict[str, float],
    thresholds: Optional[Dict[str, float]] = None,
) -> str:
    """Classify segment as accept/reject/uncomputable based on SQI metrics.
    
    Applies configurable thresholds to determine data quality. Falls back to
    defaults if thresholds not provided. Never calls external LLM.
    
    Args:
        sqi_results: Mapping of SQI metric names to computed scores.
        thresholds: Optional threshold overrides. If None, uses global settings.
    
    Returns:
        Classification string: "accept", "reject", or "uncomputable".
    
    Raises:
        ValueError: If sqi_results is empty.
    """
    if not sqi_results:
        raise ValueError("sqi_results cannot be empty")
    # implementation...
```

### README in Modules

For complex modules, include `__init__.py` docstring:

```python
# backend/app/services/__init__.py
"""
Services layer: Business logic and external integrations.

Modules:
  - storage_service: File I/O abstraction (local/GCS)
  - segment_classification_service: Rule-based SQI evaluation
  - assessment_runner: Windowed SQI computation
  - chat_grounding_service: Context retrieval for chat
"""
```

## Security Standards

1. **No secrets in code** — Use environment variables only
2. **Path traversal prevention** — Validate all file paths
3. **SQL injection prevention** — Use parameterized queries (SQLAlchemy handles)
4. **CORS policy** — Only allow frontend domain
5. **Rate limiting** — Consider adding per-user API limits (post-MVP)
6. **Input validation** — All schemas with Pydantic v2

## Performance Guidelines

1. **Database queries:** Use async SQLAlchemy with proper indexing
2. **Pagination:** Implement on listing endpoints (recordings, messages)
3. **Caching:** Use TanStack Query staleTime and cacheTime
4. **Large files:** Stream downloads (PDF exports)
5. **Agent logs:** Compact summaries (no raw waveforms)

## Accessibility (WCAG 2.1 AA)

Frontend must meet accessibility standards:

1. **Semantic HTML:** `<button>`, `<nav>`, `<main>`, `<section>`
2. **ARIA labels:** `aria-label` for icon buttons
3. **Keyboard navigation:** Tab order, focus outlines
4. **Color contrast:** Min 4.5:1 (normal text)
5. **Form labels:** Always associate labels with inputs

Example:

```typescript
<button aria-label="Close dialog" onClick={onClose}>
  <XIcon />
</button>
```

## Version Pinning

- **Python:** `requirements.txt` with exact versions
- **Node.js:** `package-lock.json` committed (lock file)
- **Critical libraries:**
  - `vital_sqi==0.1.0` (must not upgrade without testing)
  - `FastAPI==0.111.0+` (async first)
  - `Next.js==14+` (App Router required)
