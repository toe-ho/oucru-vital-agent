# 16. Testing Strategy

[← Back to Index](../00-index.md)

---

## Overview

This document defines the comprehensive testing approach for the project. Testing is organized into four layers: unit, integration, performance, and acceptance validation. All tests run automatically in CI/CD on every pull request.

**Testing Stack:**

| Layer | Backend | Frontend |
|---|---|---|
| Unit | `pytest` + `pytest-cov` | Next.js/React component tests with React Testing Library |
| Integration | `pytest` + `httpx` (async client) | User-flow tests for key frontend/backend flows |
| Performance | `pytest-benchmark`, custom timing scripts | Lighthouse CI |
| Coverage | `pytest-cov` (target: >80%) | Frontend coverage target: >80% |

---

## 1. Unit Tests

### 1.1 Backend — Tool Wrappers (8 tools)

Each agent tool is tested independently with controlled sample data. Tests mock external dependencies (LLM, database) to isolate tool logic.

**Tool wrapper test matrix:**

| Tool | Test Cases |
|---|---|
| `load_signal_file` | Valid CSV, valid Parquet, missing file, missing column, non-numeric signal values, unusual sampling rate (50 Hz, 2000 Hz) |
| `compute_sqi` | Clean ECG/PPG signal, flat-line signal, clipped signal, noisy signal, unsupported signal type |
| `compute_sqi_windowed` | All windows pass, all windows fail, mixed quality windows, short signal below one window, custom window duration |
| `preprocess_ppg` | Clean PPG, PPG with NaN values, signal below minimum length, high-frequency noise, baseline wander |
| `extract_hrv_features` | Valid RR intervals, empty RR intervals, irregular intervals, physiologically implausible intervals |
| `estimate_spo2` | Valid red/IR signals, missing channel, mismatched channel lengths, clipped channels |
| `extract_ppg_dc_layer` | Stable DC trend, drifting baseline, noisy signal, short signal |
| `check_clinical_thresholds` | Normal values, low SQI, low/high HR, low SpO2, missing optional values |

**Example test structure (pytest):**

```python
# tests/unit/test_compute_sqi.py
import pytest
import numpy as np
from app.tools.sqi_tools import compute_sqi

@pytest.fixture
def clean_ecg_segment():
    # 30-second ECG at 250 Hz
    t = np.linspace(0, 30, 30 * 250)
    return np.sin(2 * np.pi * 1.2 * t)  # synthetic ~72 bpm signal

def test_compute_sqi_returns_quality_score(clean_ecg_segment):
    result = compute_sqi(clean_ecg_segment, fs=250, signal_type="ecg")
    assert "sqi_score" in result
    assert 0 <= result["sqi_score"] <= 1

def test_compute_sqi_handles_flatline():
    flat = np.zeros(30 * 250)
    result = compute_sqi(flat, fs=250, signal_type="ecg")
    assert result["sqi_score"] < 0.4
    assert "error" not in result
```

### 1.2 Backend — API Endpoint Handlers

Test FastAPI route handlers with mocked service layer. Use `pytest` + `httpx.AsyncClient`.

**Endpoints under test:**

| Endpoint | Test Cases |
|---|---|
| `POST /api/upload` | Valid payload, missing required fields, invalid file type |
| `GET /api/results/{recording_id}` | Existing recording, non-existent recording, malformed UUID |
| `GET /api/results/{recording_id}/segments/{segment_id}` | Recording with results, recording still processing, pagination parameters |
| `GET /api/reports/{report_id}` | Report available, report not yet generated, export format (PDF/HTML) |
| `GET /health` | Always returns 200 with service status |

### 1.3 Frontend — Component Tests

Test React components in isolation using `@testing-library/react`.

**Components under test:**

| Component | Test Cases |
|---|---|
| `FileUploadDropzone` | Drag-and-drop accepted file, rejected file type, upload progress display |
| `SegmentTimelineChart` | Renders with empty data, renders N segments, color coding by classification |
| `SQIMetricsTable` | Renders all columns, sorts by metric value, filters by segment |
| `ReportExportButton` | Triggers PDF export, triggers HTML export, disabled state during generation |
| `AgentDecisionLog` | Renders tool call entries, expands/collapses reasoning, empty state |
| `ChatbotPanel` | Renders message input and send button, displays bot response, shows loading state during request, handles error state |

---

## 2. Integration Tests

### 2.1 End-to-End Pipeline (Real Recordings)

Run the full agent pipeline against real sample recordings to verify correct behavior across all stages.

**Test scenarios:**

| Scenario | Input | Expected Output |
|---|---|---|
| Clean ECG recording | 1-hour MIT-BIH ECG (NSR) | >90% segments accepted, report generated |
| Noisy ECG recording | 1-hour ECG with motion artifacts | Flagged segments with specific SQI failures identified |
| Short PPG recording | 5-minute PPG CSV | All segments processed, no crash |
| Corrupted EDF file | EDF with truncated header | Error response with `UNPROCESSABLE` status, no crash |
| Multi-channel ECG | 12-lead EDF | All channels processed, per-channel SQI reported |

**Pipeline integration test flow:**

```
1. Upload recording file → POST /api/upload
2. Trigger assessment → POST /api/assess
3. Poll assessment status → GET /api/results/{recording_id}
4. Assert status transitions: uploaded → processing → completed
5. Assert segment results stored: GET /api/results/{recording_id}
6. Assert report available: GET /api/reports/{report_id}
7. Assert report contains: summary, timeline, flagged_segments, recommendations
```

### 2.2 Full Stack Integration

Test the complete chain: database ↔ backend ↔ frontend API contract.

- Use a real PostgreSQL test instance (not mocked) via Docker Compose test profile.
- Verify all API responses conform to the OpenAPI schema.
- Assert database rows are created/updated correctly after pipeline completion.

### 2.3 Frontend ↔ Backend Communication

> **Note:** E2E tests are recommended for Phase 4+ if the team has capacity. For MVP (Phases 1–3), manual browser testing and component tests are sufficient.

Playwright E2E tests covering user flows (Phase 4+):

1. Upload a recording → see processing status → view dashboard results.
2. Navigate between Monitoring Screen and Quality Dashboard views.
3. Export report as PDF → verify file download initiated.
4. View agent decision log for a specific segment.
5. Create a segment override as `admin` or `reviewer` → verify required reason fields, dual AI/effective labels, and append-only history behavior.
6. Open chatbot panel → ask a question about a rejected segment → verify response references actual SQI values from that recording.
7. Generate a report, apply a later override, and verify the existing report shows a stale warning without auto-regeneration.

### 2.4 Chatbot Integration Tests

Test the `POST /api/chat` endpoint end-to-end with a real completed recording.

**Test scenarios:**

| Scenario | Input | Expected Output |
|---|---|---|
| Ask about rejection reason | `recording_id` + "Why was segment 3 rejected?" | Response references specific SQI metric(s) that caused rejection for segment 3 |
| Ask for overall quality summary | `recording_id` + "What is the overall signal quality?" | Response matches summary statistics from `GET /api/results/{recording_id}` |
| Ask without context | No `recording_id` + generic question | System prompts user to select a recording or returns graceful error |
| Malformed recording ID | Invalid UUID | Structured error response, no 500 crash |

**Minimum unit test coverage for chatbot:**

```python
# tests/unit/test_chat_endpoint.py
def test_chat_returns_sqi_grounded_response():
    # Mock agent_logs + sqi_results; assert response contains metric names
    ...

def test_chat_rejects_missing_recording_id():
    # POST /api/chat with no recording_id → 422 or descriptive 400
    ...
```

## 3. Performance Tests

### 3.1 Pipeline Latency (1-Hour Recording)

**Target:** Total pipeline time for a 1-hour recording < 10 minutes.

**Measurement method:**

```python
# tests/performance/test_pipeline_throughput.py
import time
from app.pipeline import run_full_pipeline

def test_one_hour_recording_under_10_minutes():
    start = time.perf_counter()
    result = run_full_pipeline("tests/fixtures/1h_ecg_mitbih.edf")
    elapsed = time.perf_counter() - start
    assert elapsed < 600, f"Pipeline took {elapsed:.1f}s, expected <600s"
    assert result.status == "COMPLETED"
```

### 3.2 Per-Segment Processing Time

**Target:** Each segment (default 30 seconds) processed in < 5 seconds (including LLM call).

Measured as: `t_classify_end - t_segment_start` for each segment in the agent loop.

### 3.3 Dashboard Load Time

**Target:** Dashboard displays results within 3 seconds of page load.

Measured with Lighthouse CI in CI/CD:

```yaml
# lighthouserc.yml
assertions:
  first-contentful-paint: ["error", {"maxNumericValue": 3000}]
  interactive: ["error", {"maxNumericValue": 3000}]
```

### 3.4 Agent Decision Latency

Track per-step LLM inference time logged by the smolagents workflow. Alert if median step latency exceeds 5 seconds.

**Metrics logged per pipeline run:**

| Metric | Target |
|---|---|
| Total pipeline wall time | < 10 min / 1-hour recording |
| Per-segment wall time | < 5 seconds |
| LLM calls per segment | ≤ 3 (bounded ReAct loop) |
| Dashboard FCP | < 3 seconds |
| API response time (GET /api/results/{recording_id}) | < 500 ms |

---

## 4. Measuring 50% Time Reduction

### 4.1 Manual Baseline Definition

The manual baseline measures time for a trained human reviewer to:

1. Load the recording in a waveform viewer.
2. Visually inspect each segment for noise, artifacts, disconnections.
3. Note problematic time windows.
4. Write a structured quality report with findings and recommendations.

**Estimated manual time:** 2–4 hours per 1-hour recording (based on domain expert input from OUCRU).

### 4.2 Measurement Protocol

```
For each benchmark recording (n=5 minimum):
  1. Record: manual_time = time for human expert to produce quality report
  2. Record: automated_time = time from file upload to report available
  3. Calculate: reduction = (manual_time - automated_time) / manual_time × 100%

Target: mean reduction ≥ 50% across all benchmark recordings
```

### 4.3 Benchmark Recording Set

| Recording ID | Source | Duration | Signal Type | Quality Profile |
|---|---|---|---|---|
| BM-001 | OUCRU anonymized | 1 hour | ECG | Mixed (some noise) |
| BM-002 | OUCRU anonymized | 1 hour | PPG | Mostly clean |
| BM-003 | MIT-BIH PhysioNet | 30 min | ECG | Clean (NSR) |
| BM-004 | MIT-BIH PhysioNet | 30 min | ECG | Noisy (motion artifacts) |
| BM-005 | Synthetic generated | 1 hour | ECG | Severe noise (sensor disconnect) |

---

## 5. Measuring 20% Precision/Recall Improvement

### 5.1 Labeled Test Dataset Requirement

A ground-truth labeled dataset is required where each segment is annotated by a human expert as:

- `accept` — segment is of sufficient quality for clinical analysis.
- `reject` — segment is too noisy or corrupted for clinical analysis.

**Minimum dataset size:** 200 labeled segments across ≥ 5 recordings.

### 5.2 Comparison Protocol

Two classifiers are compared on the same labeled dataset:

| Classifier | Description |
|---|---|
| **Baseline** | vital_sqi standalone with default `rule_dict.json` thresholds |
| **Agent-assisted** | Agent pipeline using vital_sqi + LLM reasoning + context-aware rules |

**Evaluation metrics:**

```
For each classifier:
  precision = TP / (TP + FP)
  recall    = TP / (TP + FN)
  F1        = 2 × (precision × recall) / (precision + recall)

Where positive class = accept (correctly identifying good-quality segments)
```

**Success criterion:** Agent-assisted classifier achieves ≥ 20% improvement in defect detection rate, measured as improvement in **both precision and recall** (or F1 as a composite metric). This aligns with OUCRU's original requirement of improving "quality control effectiveness by 20% in defect detection rates (precision/recall)."

### 5.3 Reporting Format

```
| Metric    | Baseline | Agent-Assisted | Improvement |
|-----------|----------|----------------|-------------|
| Precision | 0.71     | 0.86           | +21.1%      |
| Recall    | 0.68     | 0.79           | +16.2%      |
| F1-Score  | 0.69     | 0.82           | +18.8%      |
```

---

## 6. Test Data Strategy

| Data Source | Usage | Format | Volume |
|---|---|---|---|
| OUCRU anonymized recordings | Primary benchmark, acceptance testing | EDF, CSV | 5–10 recordings |
| MIT-BIH Arrhythmia Database (PhysioNet) | Unit tests, performance tests | MIT/WFDB | 48 recordings |
| MIMIC-III Waveform Database (PhysioNet) | Integration tests, edge cases | EDF | Subset |
| Synthetic generated signals | Edge case unit tests, CI/CD fixtures | NumPy arrays / CSV | Unlimited |

**Synthetic signal generation covers:**

- Flat-line (sensor disconnected).
- Clipped signal (ADC saturation).
- High-frequency noise overlay (electrical interference).
- Missing beats / long RR intervals.
- Sudden amplitude shift (electrode pop).

---

## 7. Test Environment

### 7.1 Local Development

```bash
# Run all backend tests with coverage
pytest tests/ --cov=app --cov-report=html --cov-fail-under=80

# Run frontend tests
cd frontend && npx vitest run --coverage
```

### 7.2 Docker Compose Test Profile

```yaml
# docker-compose.test.yml
services:
  db-test:
    image: postgres:15
    environment:
      POSTGRES_DB: oucru_test
  backend-test:
    build: ./backend
    depends_on: [db-test]
    command: pytest tests/integration/
  frontend-test:
    build: ./frontend
    command: npx vitest run
```

### 7.3 CI/CD Pipeline (GitHub Actions)

```
On every PR:
  1. Lint (ruff, eslint)
  2. Unit tests (backend + frontend) in parallel
  3. Integration tests (Docker Compose)
  4. Coverage report uploaded to PR comment
  5. Performance benchmarks on main branch merges only
```

### 7.4 Test Database

- Separate PostgreSQL instance for tests (never shares with development DB).
- Schema migrations applied automatically before test run.
- Database reset between test suites using transactions or fixture teardown.
