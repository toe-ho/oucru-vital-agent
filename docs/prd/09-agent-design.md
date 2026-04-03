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

The agent has access to 8 tools. Each tool is a Python function registered with the LangGraph tool registry. The agent calls them by name with typed parameters.

---

### Tool 1: `assess_ecg_quality`

**Purpose:** Execute the full ECG quality assessment pipeline in a single call — reads the file, runs preprocessing, segments, computes SQIs, and classifies each segment.

**Wraps:** `vital_sqi.get_qualified_ecg()`

**Underlying vital_sqi function signature (for reference):**
```python
# The actual vital_sqi function requires:
get_qualified_ecg(
    file_name,        # path to ECG file
    file_type,        # string: "edf" | "mit" | "csv"
    duration,         # segment duration in seconds
    sqi_dict,         # SQI metric configuration dict
    rule_dict,        # classification thresholds dict
    split_type=0,     # 0 = fixed time-based; other = beat-based
    peak_detector=6,  # default R-peak algorithm (MTEMP)
)
```

**Tool wrapper signature (simplified interface for agent):**
```python
def assess_ecg_quality(
    file_path: str,
    sampling_rate: int,
    file_type: Literal["edf", "mit", "csv"] = "edf",
    segment_duration: int = 30,
    overlap: float = 0.0,
    split_type: int = 0,
    peak_detector: int = 6,
    sqi_metrics: list[str] | None = None,
    rule_dict: dict | None = None,
) -> ECGAssessmentResult
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Absolute path to the preprocessed waveform file |
| `sampling_rate` | `int` | Samples per second (e.g., 500 Hz) |
| `file_type` | `str` | File format: `"edf"`, `"mit"`, or `"csv"` (required by underlying vital_sqi) |
| `segment_duration` | `int` | Length of each analysis window in seconds (default: 30) |
| `overlap` | `float` | Fractional overlap between consecutive segments (0.0 = no overlap) |
| `split_type` | `int` | Segmentation strategy; 0 = fixed time-based windows; other values = beat-based |
| `peak_detector` | `int` | ECG R-peak detection algorithm ID (default: 6 = MTEMP); see 14-algorithm catalog |
| `sqi_metrics` | `list[str] \| None` | List of SQI metric names to compute; None = all available |
| `rule_dict` | `dict \| None` | Classification thresholds per metric; None = default OUCRU thresholds |

**Returns:** `ECGAssessmentResult` — a typed dataclass containing:
- `segments`: list of `SegmentResult` (segment ID, start/end time, classification, SQI values dict)
- `summary`: `AssessmentSummary` (total segments, accepted count, rejected count, acceptance rate, overall quality score)
- `metadata`: dict of pipeline parameters actually applied

**Error conditions:**
- `FileNotFoundError` — file path does not exist
- `InvalidSignalTypeError` — file contains PPG signal, not ECG
- `CorruptedFileError` — file cannot be parsed or is truncated
- `vital_sqi.ProcessingError` — internal library error during SQI computation

---

### Tool 2: `assess_ppg_quality`

**Purpose:** Execute the full PPG quality assessment pipeline.

**Wraps:** `vital_sqi.get_qualified_ppg()`

**Underlying vital_sqi function signature (for reference):**
```python
# The actual vital_sqi function requires:
get_qualified_ppg(
    file_name,        # path to PPG CSV file
    signal_idx,       # positional — column index of signal in CSV (required)
    timestamp_idx,    # positional — column index of timestamps in CSV (required)
    duration,         # segment duration in seconds
    sqi_dict,         # SQI metric configuration dict
    rule_dict,        # classification thresholds dict
    split_type=0,     # 0 = fixed time-based; other = beat-based
    peak_detector=6,  # default PPG peak algorithm (DEFAULT/vitalDSP)
)
```

**Tool wrapper signature (simplified interface for agent):**
```python
def assess_ppg_quality(
    file_path: str,
    sampling_rate: int,
    signal_idx: int = 0,
    timestamp_idx: int = 1,
    segment_duration: int = 30,
    overlap: float = 0.0,
    split_type: int = 0,
    peak_detector: int = 6,
    sqi_metrics: list[str] | None = None,
    rule_dict: dict | None = None,
) -> PPGAssessmentResult
```

**Parameters:** Same structure as `assess_ecg_quality` with the following additions:

| Parameter | Type | Description |
|-----------|------|-------------|
| `signal_idx` | `int` | Column index for signal data in the PPG CSV file (positional, required by vital_sqi) |
| `timestamp_idx` | `int` | Column index for timestamps in the PPG CSV file (positional, required by vital_sqi) |
| `peak_detector` | `int` | PPG peak detection algorithm ID (default: 6 = DEFAULT/vitalDSP); see 14-algorithm catalog |

`sqi_metrics` and `rule_dict` use PPG-specific defaults.

**Returns:** `PPGAssessmentResult` — same structure as `ECGAssessmentResult` but with PPG-specific SQI metric names.

**Error conditions:** Same as `assess_ecg_quality` plus `InvalidChannelError` if required PPG channels are missing.

---

### Tool 3: `compute_ecg_sqis`

**Purpose:** Compute SQI scores only — no classification. Used when the agent wants to inspect raw metric values before applying rules, or when the researcher has requested a custom rule evaluation.

**Wraps:** `vital_sqi.get_ecg_sqis()`

**Function signature:**
```python
def compute_ecg_sqis(
    file_path: str,
    sampling_rate: int,
    segment_duration: int = 30,
    sqi_metrics: list[str] | None = None,
) -> SQIMatrix
```

**Returns:** `SQIMatrix` — a dict mapping `segment_id → {metric_name: value}` for all computed metrics. Includes up to 47+ SQI columns per segment.

**Error conditions:** Same file and library errors as `assess_ecg_quality`.

---

### Tool 4: `compute_ppg_sqis`

**Purpose:** Compute PPG SQI scores only — no classification.

**Wraps:** `vital_sqi.get_ppg_sqis()`

**Underlying vital_sqi function signature (for reference):**
```python
# The actual vital_sqi function requires signal_idx and timestamp_idx as positional params:
get_ppg_sqis(
    file_name,
    signal_idx,       # positional — column index of signal (required)
    timestamp_idx,    # positional — column index of timestamps (required)
    duration,
    sqi_dict,
)
```

**Tool wrapper signature (simplified interface for agent):**
```python
def compute_ppg_sqis(
    file_path: str,
    sampling_rate: int,
    signal_idx: int = 0,
    timestamp_idx: int = 1,
    segment_duration: int = 30,
    sqi_metrics: list[str] | None = None,
) -> SQIMatrix
```

**Returns:** `SQIMatrix` with PPG-specific metric names (e.g., `perfusion_index`, `skewness_ppg`).

---

### Tool 5: `preprocess_signal`

**Purpose:** Apply preprocessing steps to a raw waveform file and return a path to the cleaned output file. Called before SQI computation when the raw file quality is suspect.

**Wraps:** `vital_sqi` preprocessing functions (bandpass filter, trim, smooth, baseline wander removal).

**Function signature:**
```python
def preprocess_signal(
    file_path: str,
    sampling_rate: int,
    signal_type: Literal["ecg", "ppg"],
    bandpass_low: float = 0.5,
    bandpass_high: float = 40.0,
    trim_start: float = 0.0,
    trim_end: float = 0.0,
    smooth: bool = True,
) -> PreprocessResult
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `bandpass_low` | `float` | Lower cutoff frequency in Hz |
| `bandpass_high` | `float` | Upper cutoff frequency in Hz (40 Hz for ECG, 10 Hz for PPG) |
| `trim_start` | `float` | Seconds to discard from the beginning (stabilization artifact removal) |
| `trim_end` | `float` | Seconds to discard from the end |
| `smooth` | `bool` | Apply Savitzky-Golay smoothing |

**Returns:** `PreprocessResult` — contains `output_file_path` (path to cleaned file) and `operations_applied` (list of operations actually run).

**Error conditions:** `UnsupportedFormatError`, `InsufficientSignalLengthError` (signal too short after trimming).

---

### Tool 6: `generate_report`

**Purpose:** Compose a structured quality report combining quantitative SQI statistics and the agent's narrative interpretation. Stores the report and returns its ID.

**Wraps:** Custom `ReportService` (not `vital_sqi`).

**Function signature:**
```python
def generate_report(
    recording_id: str,
    assessment_result: ECGAssessmentResult | PPGAssessmentResult,
    agent_interpretation: str,
    format: Literal["pdf", "html"] = "html",
    include_waveform_plots: bool = True,
) -> ReportResult
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | `str` | UUID of the recording; used to link the report in the database |
| `assessment_result` | `ECGAssessmentResult \| PPGAssessmentResult` | Full pipeline output from assess tools |
| `agent_interpretation` | `str` | Agent's narrative text: patterns observed, anomalies flagged, recommendations |
| `format` | `Literal["pdf", "html"]` | Output format |
| `include_waveform_plots` | `bool` | Whether to render segment waveform thumbnails in the report |

**Returns:** `ReportResult` — contains `report_id`, `file_path`, `generated_at` timestamp.

**Error conditions:** `ReportRenderError` (template or PDF engine failure), `StorageError`.

---

### Tool 7: `query_history`

**Purpose:** Retrieve past assessment results for a patient or device to enable trend analysis and longitudinal comparison.

**Wraps:** Custom `DatabaseService` (not `vital_sqi`).

**Function signature:**
```python
def query_history(
    subject_id: str | None = None,
    device_id: str | None = None,
    signal_type: Literal["ecg", "ppg"] | None = None,
    limit: int = 10,
    since: datetime | None = None,
) -> list[AssessmentHistoryEntry]
```

**Returns:** List of `AssessmentHistoryEntry` — each contains `recording_id`, `assessment_date`, `acceptance_rate`, `overall_quality_score`, `signal_type`.

**Error conditions:** `DatabaseConnectionError`, `InvalidQueryError` (both `subject_id` and `device_id` are None).

---

### Tool 8: `get_segment_detail`

**Purpose:** Retrieve the full SQI breakdown and raw waveform data for a specific segment. Used when the agent needs to explain a rejection decision or investigate an anomaly.

**Wraps:** Custom `DatabaseService` + file storage read.

**Function signature:**
```python
def get_segment_detail(
    recording_id: str,
    segment_id: str,
) -> SegmentDetail
```

**Returns:** `SegmentDetail` — contains:
- `segment_id`, `segment_number`, `start_time`, `end_time`
- `classification`: `"accepted"` | `"rejected"`
- `sqi_values`: full dict of all computed metrics for this segment
- `failed_rules`: list of `RuleViolation` (metric, actual value, threshold, operator)
- `waveform_data`: list of raw sample values for rendering

**Error conditions:** `SegmentNotFoundError`, `StorageError`.

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
│  ACT: Call appropriate pipeline tool                            │
│       → If ECG: assess_ecg_quality(file_path, ...)             │
│       → If PPG: assess_ppg_quality(file_path, ...)             │
│       → If raw/unfiltered: preprocess_signal() first           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVE: Receive tool results                                  │
│           - SQI matrix (segments × metrics)                     │
│           - Classification per segment (accepted / rejected)    │
│           - Summary statistics                                  │
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
│  ACT: Generate report    │       │  ACT: Call get_segment_detail  │
│  generate_report(...)    │       │  for each flagged segment      │
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
- assess_ecg_quality: Run the full ECG quality assessment pipeline (preprocessing → segmentation → SQI computation → classification)
- assess_ppg_quality: Run the full PPG quality assessment pipeline
- compute_ecg_sqis: Compute SQI scores for ECG segments without classification (use when custom rule evaluation is needed)
- compute_ppg_sqis: Compute SQI scores for PPG segments without classification
- preprocess_signal: Apply bandpass filtering, trimming, and smoothing to a raw waveform file
- generate_report: Compose and store a structured quality report
- query_history: Retrieve past assessment results for trend comparison
- get_segment_detail: Get full SQI breakdown and waveform data for a specific segment

## Decision Guidelines

### When to use the full pipeline (assess_ecg_quality / assess_ppg_quality)
- Use this for the majority of assessments. It handles preprocessing, segmentation, SQI computation,
  and classification in a single call.
- Prefer this unless there is a specific reason to decompose the pipeline.

### When to use compute_*_sqis without classification
- When the researcher has requested a custom rule evaluation with non-standard thresholds.
- When you want to inspect the raw SQI values before deciding which rule_dict to apply.

### When to call preprocess_signal first
- When the file metadata indicates it came from a field device without onboard filtering.
- When initial SQI scores are uniformly poor (possible baseline wander or high-frequency noise artifact).

### When to call get_segment_detail
- When the acceptance rate is unexpectedly low and you need to understand which specific metrics
  are failing and why.
- When answering a user question about a specific segment (chatbot mode).

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

## 6. Recommended Framework: LangGraph

**Recommendation: LangGraph** (preferred), with LangChain as the underlying tool/prompt abstraction layer.

### Why LangGraph over plain LangChain

| Concern | LangChain (LCEL / AgentExecutor) | LangGraph |
|---------|----------------------------------|-----------|
| State management | Implicit, passed through callbacks | Explicit typed state dict shared across all nodes |
| Flow control | Difficult to add conditional branches | Native conditional edges and loops |
| Debugging | Hard to trace mid-run state | State is inspectable at every node boundary |
| Resumability | Not supported | Can checkpoint and resume at any node |
| Multi-step pipelines | Verbose to express | Natural as a graph of nodes |
| Learning curve | Lower initially | Slightly higher, but much better for complex flows |

**For this project**, the 10-step pipeline with conditional branching (e.g., preprocess first vs. direct assessment, normal completion vs. escalation) maps directly to a LangGraph state machine. LangChain's `AgentExecutor` would require brittle callback chains to achieve the same control flow.

**Learning value**: Understanding LangGraph teaches students the fundamentals of agentic architectures (state machines, tool registries, conditional routing) that generalize to production systems.

### Suggested LangGraph Node Structure

```
[start] → [analyze_metadata] → [preprocess?] → [run_pipeline] →
[interpret_results] → [needs_detail?] → [fetch_details] →
[generate_report] → [finalize_or_escalate] → [end]
```

Conditional edges:
- `preprocess?` → run `preprocess_signal` only if `state.needs_preprocessing`
- `needs_detail?` → loop to `fetch_details` for each flagged segment, then back to `generate_report`
- `finalize_or_escalate` → route to escalation node if `state.escalate == True`

---

## 7. LLM Provider Strategy

### Architecture: Abstract Base Provider

All LLM interactions go through a provider abstraction layer. This enables switching between LLM backends via configuration and makes it trivial to add new providers.

```python
# backend/app/agent/llm/base_provider.py
from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.
    Extend this class to add new LLM backends (OpenAI, Claude, Mistral, etc.)."""

    @abstractmethod
    async def invoke(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Send messages to the LLM and return the response."""
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], tools: list[dict] | None = None):
        """Stream responses token-by-token (for chatbot)."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier for logging."""
        ...
```

```python
# backend/app/agent/llm/gemini_provider.py
from google.cloud import aiplatform
from .base_provider import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    """Google Gemini via Vertex AI. Primary provider — covered by GCP credits."""
    ...

# backend/app/agent/llm/ollama_provider.py
from .base_provider import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    """Ollama self-hosted. Optional fallback for offline/demo use."""
    ...
```

```python
# backend/app/agent/llm/factory.py
def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function. Reads LLM_PROVIDER env var if not specified."""
    provider = provider_name or os.getenv("LLM_PROVIDER", "gemini")
    if provider == "gemini":
        return GeminiProvider()
    elif provider == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
```

#### Primary: Google Gemini 2.0 Flash (Vertex AI)

| Attribute | Detail |
|-----------|--------|
| Model | Gemini 2.0 Flash |
| Access | Vertex AI API (Google Cloud) |
| Cost | Covered by existing $2-3K GCP credits |
| Tool-calling | Excellent — native function calling support |
| Latency | ~1-2s per call |
| Setup | Enable Vertex AI API, set `GOOGLE_CLOUD_PROJECT` env var |

**Why Gemini as primary:**
- GCP credits already available — zero additional cost
- Superior tool-calling reliability compared to open-source 8B models
- No GPU infrastructure needed — saves credits for compute/storage
- LangGraph has built-in Vertex AI / Gemini integration via `langchain-google-vertexai`

#### Fallback: Ollama (Self-hosted, Optional)

| Attribute | Detail |
|-----------|--------|
| Model | Llama 3.1 8B Instruct (quantized) |
| Access | Local Ollama server |
| Cost | Free (CPU) or GPU time from GCP credits |
| Tool-calling | Good with Llama 3.1 8B |
| Latency | ~3-10s per call (CPU), ~1-3s (GPU) |
| Setup | `docker compose --profile local-llm up` |

**When to use Ollama:**
- Offline development without internet
- Demo environments without GCP access
- GCP credits exhausted
- Testing provider-switching logic

#### Adding New Providers

To add a new LLM provider (e.g., OpenAI, Claude, Mistral):
1. Create `backend/app/agent/llm/{provider}_provider.py`
2. Extend `BaseLLMProvider`
3. Implement `invoke()`, `stream()`, `get_model_name()`
4. Register in `factory.py`
5. Set `LLM_PROVIDER={provider}` in `.env`

### Budget Analysis (GCP Credits ~$2,000–$3,000)

| Resource | Spec | Monthly Cost Estimate |
|----------|------|-----------------------|
| Vertex AI API (Gemini 2.0 Flash) | ~1,000–2,000 input tokens + ~500 output tokens per assessment | ~$5–$20/month |
| Cloud SQL (PostgreSQL) | db-f1-micro, 10 GB SSD | ~$10–$15/month |
| Cloud Storage | 50 GB file storage | ~$1/month |
| Cloud Run (CPU, frontend + backend) | 2 vCPU, 4 GB RAM | ~$30–$50/month |
| **Total estimated** | | **~$50–$90/month** |

Switching from a self-hosted T4 GPU VM to Gemini API reduces monthly cloud cost by ~60%, freeing budget for compute and storage. With $2,000 in credits and ~$70/month burn rate, the system runs for approximately **24–28 months** — well beyond the capstone timeline.

---

## 8. Agent Memory and State Management

The agent uses a **LangGraph TypedDict state** that is passed between nodes and updated at each step. This is the primary mechanism for tracking progress across the multi-step pipeline.

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
| Tool call | `"assess_ecg_quality"` | Why this tool was chosen | All parameters passed |
| Tool result | NULL | Agent's interpretation of the result | NULL (result in output_summary) |
| Decision | NULL | Decision rationale and verdict | NULL |
| Escalation | NULL | Full escalation reason | NULL |

This log provides complete transparency for clinical audits, debugging of unexpected assessment outcomes, and training data for future model fine-tuning.

---

## 10. Token-Encoding Privacy Layer

The token-encoding privacy layer is a **core component** that intercepts every prompt sent from the agent to the external LLM and every response received back. Its purpose is to ensure no patient-identifiable information (subject IDs, device IDs, recording filenames, timestamps) is transmitted in plain text to the LLM process.

### How It Works

1. **Before each LLM call**: the layer scans the outgoing prompt for registered sensitive tokens (drawn from the current `AgentState` — `subject_id`, `device_id`, `recording_id`, `file_path`). Each sensitive value is replaced with a deterministic placeholder (e.g., `SUBJ-042` → `__SUBJECT_0__`, `DEV-007` → `__DEVICE_0__`). A session-scoped mapping table is kept in memory.

2. **The LLM receives and reasons over only the placeholder tokens.** Its tool call arguments and reasoning text will reference `__SUBJECT_0__` rather than `SUBJ-042`.

3. **After each LLM response**: the layer applies the reverse mapping, replacing all placeholders with their original values before the response is stored in `AgentState`, written to `AgentLogs`, or returned to the API layer.

### Implementation Location

`backend/app/agent/privacy_layer.py` — a stateless utility class instantiated per agent invocation. The LangGraph node responsible for LLM calls (`interpret_results`, `chatbot_response`) wraps all `llm.invoke()` / `llm.astream()` calls through this layer.

### Scope of Encoding

| Field | Encoding applied |
|-------|-----------------|
| `subject_id` | Yes — replaced with `__SUBJECT_N__` |
| `device_id` | Yes — replaced with `__DEVICE_N__` |
| `recording_id` (UUID) | Yes — replaced with `__RECORDING_N__` |
| `file_path` | Yes — path stripped to basename, then encoded |
| SQI metric names | No — these are non-identifying numeric column names |
| Segment time offsets | No — relative time values carry no PII |

### Chatbot Mode

When the agent handles a `POST /api/chat` request, the token-encoding layer is active for the full conversation turn. The user's question may contain references to segment numbers or metric names — these are passed through unchanged (they carry no PII). Any `subject_id` or `recording_id` injected into the system prompt for context is encoded before the LLM call and decoded in the response.

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
2. LangGraph node catches the exception.
3. **Retry strategy**: exponential backoff — retry after 2s, 4s, 8s (max 3 retries).
4. If all retries fail: fall back to **rule-based assessment mode** — run the `vital_sqi` pipeline directly using default parameters, skip the LLM interpretation, and generate a reduced report with only quantitative statistics and no narrative.
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
