# 09 — Agent Design

[← Back to Index](00-index.md)

---

## 1. Agent Overview

The agent is an **LLM-powered autonomous system** that orchestrates OUCRU's `vital_sqi` library to perform end-to-end waveform quality assessment. It is the "brain" of the system; `vital_sqi` is the "toolbox".

The key architectural principle is **strict separation of concerns**:
- The agent decides **what** to do and **why**: which pipeline to run, which segments to investigate, when to escalate.
- The tools (wrappers around `vital_sqi`) decide **how** to do it: signal filtering, segmentation, SQI computation, classification.
- The agent **never** performs signal processing directly. It only calls tools and reasons about their outputs.

This design makes the agent's logic testable independently of `vital_sqi`, allows tool implementations to be swapped without rewriting agent prompts, and produces a transparent audit trail of every decision.

---

## 2. Agent Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Pipeline orchestration** | Determine the correct sequence of tool calls for a given file type (ECG vs. PPG) and invoke them in order |
| **SQI interpretation** | Read the SQI matrix returned by `vital_sqi` and identify patterns: low acceptance rate, clustered rejections, temporal degradation, outlier metric values |
| **Quality assessment decisions** | Determine the overall quality verdict (acceptable / marginal / poor) based on acceptance rate thresholds and agent reasoning |
| **Report generation** | Compose a structured quality report combining quantitative SQI statistics with narrative interpretation and recommendations |
| **Error handling and recovery** | Detect tool failures, decide whether to retry, fall back to a degraded mode, or escalate to a human operator |
| **Escalation** | Flag recordings that require human review (e.g., acceptance rate < 40%, corrupted file segments, anomalous SQI patterns not covered by rules) |
| **Logging** | Record every tool call, input, output, and reasoning step to the `AgentLogs` table for full auditability |

---

## 3. Agent Tools

The agent has access to 8 OUCRU analysis tools. Each tool is a Python function registered with the agent tool registry. The agent calls them by name with typed parameters.

---

### Tool 1: `load_signal_file`

**Purpose:** Load a physiological waveform from CSV or Parquet so later tools can operate on numeric arrays rather than file paths.

**Function signature:**
```python
def load_signal_file(
    file_path: str,
    column: str = "ppg",
    fs: int = 100,
) -> dict
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the uploaded CSV or Parquet waveform file |
| `column` | `str` | Signal column to load; default `"ppg"` |
| `fs` | `int` | Sampling rate in Hz; default `100` |

**Returns:** Signal samples and sampling metadata for downstream tools.

---

### Tool 2: `compute_sqi`

**Purpose:** Compute a single overall signal quality score for ECG or PPG. The agent uses this as the first quality gate before heavier analysis.

**Function signature:**
```python
def compute_sqi(
    signal: list[float],
    fs: int = 100,
    signal_type: Literal["ecg", "ppg"] = "ppg",
) -> dict
```

**Returns:** A structured result containing an SQI score in the 0–1 range and related quality metadata.

---

### Tool 3: `compute_sqi_windowed`

**Purpose:** Compute signal quality over fixed windows so the agent can identify poor-quality segments and temporal degradation.

**Function signature:**
```python
def compute_sqi_windowed(
    signal: list[float],
    fs: int = 100,
    signal_type: Literal["ecg", "ppg"] = "ppg",
    window_sec: int = 30,
) -> dict
```

**Returns:** Per-window SQI results that can be converted into accepted, rejected, or low-confidence segment labels by rule evaluation.

---

### Tool 4: `preprocess_ppg`

**Purpose:** Filter, normalize, and detect peaks in PPG signals before PPG-specific feature extraction.

**Function signature:**
```python
def preprocess_ppg(
    signal: list[float],
    fs: int = 100,
) -> dict
```

**Returns:** Processed PPG samples, detected peaks, and preprocessing metadata.

---

### Tool 5: `extract_hrv_features`

**Purpose:** Extract HRV features from RR intervals after usable peaks have been identified.

**Function signature:**
```python
def extract_hrv_features(
    rr_intervals_ms: list[float],
    fs: int = 100,
) -> dict
```

**Returns:** Time-domain and frequency-domain HRV features for clinical interpretation.

---

### Tool 6: `estimate_spo2`

**Purpose:** Estimate oxygen saturation when red and infrared PPG channels are available.

**Function signature:**
```python
def estimate_spo2(
    red_signal: list[float],
    ir_signal: list[float],
    fs: int = 100,
) -> dict
```

**Returns:** Estimated SpO2 percentage and supporting signal statistics.

---

### Tool 7: `extract_ppg_dc_layer`

**Purpose:** Extract the DC component of a PPG signal for perfusion and trend analysis.

**Function signature:**
```python
def extract_ppg_dc_layer(
    signal: list[float],
    fs: int = 100,
) -> dict
```

**Returns:** DC-layer trend values and summary statistics.

---

### Tool 8: `check_clinical_thresholds`

**Purpose:** Convert numeric outputs such as heart rate, SpO2, and SQI into structured flags that the agent can interpret and escalate.

**Function signature:**
```python
def check_clinical_thresholds(
    heart_rate_bpm: float | None = None,
    spo2_pct: float | None = None,
    sqi_score: float | None = None,
) -> dict
```

**Returns:** Threshold pass/fail flags, severity labels, and clinical/quality notes.

---

## 4. Agent Decision Loop (ReAct Pattern)

The agent operates on a Reasoning + Acting (ReAct) loop. Each iteration consists of an OBSERVE → THINK → ACT cycle. The loop terminates when the agent determines the assessment is complete or when it escalates to a human.

```
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE: Receive new file notification or user request         │
│           Input: { recording_id, file_path, signal_type,        │
│                    sampling_rate, subject_id }                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THINK: Analyze file metadata                                   │
│         - Is this ECG or PPG?                                   │
│         - Is the file format valid (EDF/CSV)?                   │
│         - Does sampling_rate look correct for this signal type? │
│         - Is preprocessing needed (raw file from field device)? │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  ACT: Call appropriate OUCRU tools                              │
│       → load_signal_file(file_path, column, fs)                 │
│       → compute_sqi(signal, fs, signal_type)                    │
│       → compute_sqi_windowed(...) for segment-level quality     │
│       → If PPG raw/unfiltered: preprocess_ppg() first           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE: Receive tool results                                  │
│           - Overall SQI score                                   │
│           - Windowed SQI values for segment-level quality       │
│           - Clinical/quality threshold flags                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THINK: Interpret results                                       │
│         - What is the overall acceptance rate?                  │
│         - Are rejections clustered (points to device artifact)? │
│         - Is there temporal degradation (quality trends down)?  │
│         - Which SQI metrics are most frequently out of range?   │
│         - Are there segments with borderline scores to flag?    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
               ┌───────────────┴──────────────────┐
               │ normal case                       │ needs detail
               ▼                                   ▼
┌──────────────────────────┐       ┌───────────────────────────────┐
│  ACT: Generate report    │       │  ACT: Inspect windowed SQI     │
│  from persisted results  │       │  and threshold flags           │
└──────────────┬───────────┘       └──────────────┬────────────────┘
               │                                  │
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE: Report generated / Detail retrieved                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  THINK: Is assessment complete?                                 │
│         - Acceptance rate > 40% AND no anomalous patterns       │
│           → COMPLETE, finalize                                  │
│         - Acceptance rate < 40% OR critical SQI failures        │
│           → ESCALATE to human reviewer                          │
│         - Unrecoverable tool error                              │
│           → ESCALATE with partial results                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  ACT: Finalize                                                  │
│       - Persist results to database                             │
│       - Update recording status to "completed" or "escalated"  │
│       - Trigger dashboard notification                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Agent Prompt Design

### System Prompt Template

```
You are an autonomous clinical waveform quality monitoring agent deployed at the Oxford University
Clinical Research Unit (OUCRU). Your role is to assess the signal quality of ECG and PPG recordings
collected during research studies and clinical trials.

## Your Capabilities
You have access to the following tools:
- load_signal_file: Load CSV or Parquet waveform data into numeric samples with sampling metadata
- compute_sqi: Compute an overall ECG or PPG quality score
- compute_sqi_windowed: Compute per-window SQI values for segment-level quality analysis
- preprocess_ppg: Filter, normalize, and detect peaks in PPG signals
- extract_hrv_features: Extract HRV features from RR intervals
- estimate_spo2: Estimate oxygen saturation from red and infrared PPG channels
- extract_ppg_dc_layer: Extract the PPG DC component for perfusion and trend analysis
- check_clinical_thresholds: Flag heart rate, SpO2, or SQI values outside configured thresholds

## Decision Guidelines

### Standard quality-assessment sequence
- Start with `load_signal_file` to load the configured waveform column and sampling rate.
- Call `compute_sqi` to obtain an overall ECG or PPG quality score.
- Call `compute_sqi_windowed` when segment-level quality, timeline overlays, or clustered artifact detection are needed.
- Call `check_clinical_thresholds` to convert SQI, heart rate, or SpO2 outputs into structured flags.

### When to call `preprocess_ppg` first
- When PPG metadata indicates the file came from a field device without onboard filtering.
- When initial PPG SQI scores are uniformly poor, suggesting baseline wander or high-frequency noise.

### When to call PPG/clinical feature tools
- Call `extract_hrv_features` when usable RR intervals are available and HRV interpretation is requested.
- Call `estimate_spo2` only when red and infrared PPG channels are present.
- Call `extract_ppg_dc_layer` when perfusion or slow trend analysis is needed.

### When to escalate
- Acceptance rate below 40% after a full assessment.
- More than 3 consecutive hours of rejected segments (severe artifact or device failure).
- File corruption preventing completion of any pipeline step.
- SQI values that are physically implausible (e.g., mean HR < 20 or > 250 BPM).

## Output Format
When you have completed an assessment, produce your interpretation as a JSON object:
{
  "assessment_complete": true,
  "overall_verdict": "acceptable" | "marginal" | "poor",
  "acceptance_rate": <float 0–1>,
  "key_findings": ["<finding 1>", "<finding 2>", ...],
  "flagged_segments": [<segment_id>, ...],
  "recommendations": ["<recommendation 1>", ...],
  "escalate": true | false,
  "escalation_reason": "<string if escalate is true>"
}

## Safety Constraints
- NEVER modify or overwrite the original raw waveform file. Read-only access only.
- ALWAYS log every tool call with its parameters and the reasoning behind calling it.
- NEVER fabricate SQI values or classification results. Report tool errors as errors.
- If a tool returns an error, log it and decide whether to retry, use a fallback approach,
  or escalate. Do not proceed as if the tool succeeded.
- When uncertain about signal type or file format, ask for clarification rather than guessing.
```

---

## 6. Recommended Framework: smolagents

**Recommendation: smolagents** for agent orchestration.

### Why smolagents

| Concern | smolagents fit |
|---------|----------------|
| Tool control | The agent can call only approved Python tools registered in the tool list |
| Simplicity | Minimal orchestration layer for a capstone team; fewer moving parts than graph frameworks |
| Local LLM support | Works well with Ollama-backed local models such as Qwen3-8B |
| Auditability | Each tool call can be logged with arguments, result summary, and reasoning |
| Workflow flexibility | YAML task plans and `config.yaml` can drive task order, thresholds, and model settings |

**For this project**, the agent receives a task plan, loads the approved OUCRU tools, asks Qwen3-8B through Ollama to choose tool calls, and records each step to `AgentLogs`. The backend remains responsible for persistence, report generation, API responses, and access control.

### Suggested smolagents Workflow

```
[user/API request]
  → load YAML task plan + config.yaml
  → build system prompt with workflow rules and thresholds
  → initialize smolagents CodeAgent with approved tools
  → run tool-call loop through Ollama + Qwen3-8B
  → validate structured JSON output
  → persist SQI/window results, report metadata, and agent logs
```

Workflow rules:
- Always call `load_signal_file` before numeric analysis.
- Call `preprocess_ppg` only for PPG signals when preprocessing is needed.
- Call `compute_sqi` for overall quality and `compute_sqi_windowed` for segment/window quality.
- Call clinical feature tools only when their required inputs are available.
- Escalate or return low confidence when tool errors or low SQI values prevent reliable interpretation.

---

## 7. LLM Runtime Strategy

### Primary Runtime: Ollama + Qwen3-8B

| Attribute | Detail |
|-----------|--------|
| Model | Qwen3-8B |
| Serving | Ollama local runtime |
| Role | Workflow planning, tool selection, report explanation, and chatbot Q&A |
| Configuration | `config.yaml` stores model name, base URL, temperature, max tokens, agent step limit, and thresholds |
| Privacy | Runs locally through Ollama; input files are assumed de-identified before upload and raw waveform arrays are not sent to the LLM |

**Why Ollama + Qwen3-8B:**
- Matches the local-first capstone workflow.
- Avoids dependency on external LLM APIs during development and demos.
- Keeps model settings reproducible through `config.yaml`.
- Works with smolagents and approved Python tool calls.

### Budget Analysis

| Resource | Spec | Monthly Cost Estimate |
|----------|------|-----------------------|
| Ollama runtime | Qwen3-8B on local machine or project-controlled compute | Depends on host; no per-token API cost |
| Cloud SQL (PostgreSQL) | db-f1-micro, 10 GB SSD | ~$10–$15/month |
| Cloud Storage | 50 GB file storage | ~$1/month |
| Cloud Run (frontend + backend) | Small autoscaling services | ~$30–$50/month |
| **Total estimated excluding LLM host** | | **~$40–$70/month** |

---

## 8. Agent Memory and State Management

The agent uses a structured Python state object that is updated after each smolagents step. This is the primary mechanism for tracking progress across the multi-step pipeline.

### State Schema

```python
from typing import TypedDict, Literal

class AgentState(TypedDict):
    # Input
    recording_id: str
    file_path: str
    signal_type: Literal["ecg", "ppg"]
    sampling_rate: int
    subject_id: str | None

    # Processing stage
    current_stage: Literal[
        "initialized", "preprocessing", "assessing",
        "interpreting", "fetching_details", "generating_report",
        "finalizing", "escalated", "completed", "error"
    ]
    needs_preprocessing: bool

    # Intermediate results
    preprocessed_file_path: str | None
    assessment_result: dict | None        # serialized ECGAssessmentResult / PPGAssessmentResult
    sqi_matrix: dict | None               # segment_id → {metric: value}
    flagged_segment_ids: list[str]
    segment_details: dict[str, dict]      # segment_id → SegmentDetail

    # Agent reasoning
    agent_interpretation: str | None      # agent's narrative text
    key_findings: list[str]
    recommendations: list[str]

    # Decisions
    overall_verdict: Literal["acceptable", "marginal", "poor"] | None
    acceptance_rate: float | None
    escalate: bool
    escalation_reason: str | None

    # Output
    report_id: str | None
    error_message: str | None
    tool_call_count: int
```

**State persistence:** After each node completes, the state is serialized and written to the `AgentLogs` table (linked to `recording_id`). This allows the assessment to be resumed if interrupted (e.g., container restart) and provides the audit trail.

---

## 9. Agent Logging

Every tool call, reasoning step, and decision is logged to the `AgentLogs` table.

### AgentLogs Table Schema

```sql
CREATE TABLE agent_logs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recording_id UUID NOT NULL REFERENCES recordings(id),
    step_number  INTEGER NOT NULL,
    timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stage        TEXT NOT NULL,
    tool_called  TEXT,              -- NULL if this is a reasoning step, not a tool call
    input_params JSONB,             -- parameters passed to the tool
    output_summary TEXT,            -- brief text summary of tool output
    reasoning    TEXT,              -- agent's THINK step text for this iteration
    duration_ms  INTEGER,           -- tool execution time in milliseconds
    success      BOOLEAN NOT NULL,
    error_detail TEXT               -- populated if success = false
);
```

### What is logged

| Event type | `tool_called` | `reasoning` | `input_params` |
|------------|---------------|-------------|----------------|
| THINK step | NULL | Full LLM reasoning text | NULL |
| Tool call | `"compute_sqi_windowed"` | Why this tool was chosen | All parameters passed |
| Tool result | NULL | Agent's interpretation of the result | NULL (result in output_summary) |
| Decision | NULL | Decision rationale and verdict | NULL |
| Escalation | NULL | Full escalation reason | NULL |

This log provides complete transparency for clinical audits, debugging of unexpected assessment outcomes, and training data for future model fine-tuning.

---

## 11. Error Handling

### Corrupted or Unreadable File

1. `vital_sqi` raises `CorruptedFileError` or `FileNotFoundError`.
2. Agent catches the exception in the tool wrapper.
3. Tool returns a structured error result: `{ "success": false, "error_type": "CorruptedFileError", "detail": "..." }`.
4. Agent logs the error with full detail.
5. Agent sets `state.current_stage = "error"` and `state.escalate = True`.
6. Agent generates a minimal error report notifying the researcher that the file could not be processed.
7. Dashboard shows recording status as `"error"` with the error message.

### LLM Inference Failure

1. LLM API call times out or returns a non-parseable response.
2. The smolagents workflow catches the exception.
3. **Retry strategy**: exponential backoff — retry after 2s, 4s, 8s (max 3 retries).
4. If all retries fail: fall back to **rule-based assessment mode** — run the OUCRU signal tools directly using default parameters, skip the LLM interpretation, and generate a reduced report with only quantitative statistics and no narrative.
5. Log that the report was generated in fallback mode.

### Pipeline Timeout

1. Each tool call has a configurable timeout (default: 120 seconds for full pipeline, 30 seconds for detail queries).
2. If a tool call exceeds the timeout, it is cancelled via `asyncio.wait_for`.
3. Agent logs the timeout, marks the recording as `"partial"`, and generates a partial results report covering the segments processed before the timeout.
4. Researcher is notified via dashboard alert.

### Escalation Triggers Summary

| Condition | Escalation Type |
|-----------|----------------|
| Acceptance rate < 40% | Soft escalation — flag for human review, assessment still completes |
| 3+ consecutive rejected segments spanning > 30 minutes | Soft escalation — annotated in report |
| File corruption preventing any processing | Hard escalation — no report, only error notification |
| Physically implausible SQI values (HR < 20 or > 250 BPM) | Soft escalation — flagged in report |
| LLM fallback mode activated | Informational flag — report marked as "auto-generated, no AI interpretation" |
