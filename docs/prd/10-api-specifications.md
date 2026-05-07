# 10 — API Specifications

[← Back to Index](00-index.md)

---

## Overview

**Scope:** All endpoints handle waveform data (ECG, PPG) only. Imaging support is deferred to future phases.

All endpoints are served by the FastAPI backend at base URL `/api`. Request and response bodies use `application/json` unless noted. File uploads use `multipart/form-data`.

### Standard Error Response

All error responses share this structure:

```json
{
  "error": "NotFound",
  "detail": "Recording with id 'abc123' does not exist."
}
```

### HTTP Status Codes Used

| Code | Meaning |
|------|---------|
| `200` | Success — resource returned or action completed |
| `201` | Created — new resource created |
| `202` | Accepted — request accepted for asynchronous processing |
| `400` | Bad Request — invalid parameters or malformed body |
| `404` | Not Found — resource does not exist |
| `422` | Unprocessable Entity — FastAPI validation error (field type mismatch, missing required field) |
| `500` | Internal Server Error — unexpected backend or agent failure |

---

## Endpoints

---

### POST /api/upload

Upload a waveform file and register it as a new recording.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | yes | EDF, MIT/WFDB bundle, CSV, or Parquet waveform file |
| `signal_type` | string | yes | `"ecg"` or `"ppg"` |
| `sampling_rate` | number | yes | Samples per second (e.g., `500`) |
| `subject_id` | string | no | Anonymized patient or subject identifier |
| `device_id` | string | no | Device identifier for provenance tracking |
| `notes` | string | no | Free-text notes from the researcher |

**Response `201`:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "filename": "subject_042_ecg_2024-11-15.edf",
  "status": "uploaded",
  "metadata": {
    "signal_type": "ecg",
    "sampling_rate": 500,
    "file_size_bytes": 14680064,
    "duration_seconds": 3600,
    "subject_id": "SUBJ-042",
    "device_id": "DEV-007",
    "uploaded_at": "2024-11-15T08:32:11Z"
  }
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `400` | Unsupported file format (not EDF, MIT/WFDB, CSV, or Parquet) |
| `400` | `signal_type` is not `"ecg"` or `"ppg"` |
| `400` | `sampling_rate` is zero or negative |
| `500` | File storage write failure |

---

### POST /api/assess

Trigger a quality assessment for an uploaded recording. The assessment runs asynchronously; the response returns immediately with a job identifier.

**Request:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "config": {
    "segment_duration": 30,
    "overlap": 0.0,
    "split_type": 0,
    "sqi_metrics": [
      "kurtosis", "skewness", "snr", "mean_hr", "sdnn",
      "rmssd", "pnn50", "lf_hf_ratio"
    ],
    "rule_dict": {
      "mean_hr":    { "min": 40, "max": 200 },
      "sdnn":       { "min": 7.93, "max": 676 },
      "kurtosis":   { "min": -1.5, "max": 10.0 }
    }
  }
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recording_id` | string (UUID) | yes | ID returned by `/api/upload` |
| `config.segment_duration` | integer | no | Window length in seconds; default `30` |
| `config.overlap` | float | no | Fractional overlap `[0.0, 1.0)`; default `0.0` |
| `config.split_type` | integer | no | Segmentation strategy; `0` = fixed-length; default `0` |
| `config.sqi_metrics` | array of string | no | Metrics to compute; omit for all available |
| `config.rule_dict` | object | no | Per-metric thresholds; omit for OUCRU defaults |

**Response `202`:**

```json
{
  "assessment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "processing",
  "estimated_duration_seconds": 45
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `400` | Recording status is not `"uploaded"` (already assessed or in error state) |
| `400` | `segment_duration` is zero or negative |
| `400` | `overlap` is not in range `[0.0, 1.0)` |

---

### GET /api/results/{recording_id}

Retrieve the assessment results for a recording. Poll this endpoint to check processing status.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | string (UUID) | Recording identifier |

**Response `200` (assessment complete):**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "assessment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "signal_type": "ecg",
  "assessed_at": "2024-11-15T08:33:05Z",
  "summary": {
    "total_segments": 120,
    "accepted": 98,
    "rejected": 22,
    "acceptance_rate": 0.817,
    "overall_quality_score": 0.79,
    "verdict": "acceptable"
  },
  "segments": [
    {
      "segment_id": "seg-001",
      "segment_number": 1,
      "start_time": 0,
      "end_time": 30,
      "classification": "accepted",
      "sqi_summary": {
        "kurtosis": 3.14,
        "skewness": 0.12,
        "snr": 18.7,
        "mean_hr": 72.3
      }
    },
    {
      "segment_id": "seg-045",
      "segment_number": 45,
      "start_time": 1320,
      "end_time": 1350,
      "classification": "rejected",
      "sqi_summary": {
        "kurtosis": 12.8,
        "skewness": 2.41,
        "snr": 4.2,
        "mean_hr": 68.1
      }
    }
  ],
  "agent_interpretation": "The recording shows good overall quality with an acceptance rate of 81.7%. A cluster of rejected segments was observed between t=1320s and t=1500s (segments 45–50), likely attributable to motion artifact. The final 10 minutes show recovery to baseline quality.",
  "escalated": false
}
```

**Response `200` (still processing):**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "processing",
  "progress": {
    "current_stage": "assessing",
    "segments_processed": 60,
    "total_segments": 120
  }
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `500` | Assessment failed with an internal error; `status` will be `"error"` with `error_detail` |

---

### GET /api/results/{recording_id}/segments/{segment_id}

Retrieve the full SQI breakdown and raw waveform data for a single segment.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | string (UUID) | Recording identifier |
| `segment_id` | string | Segment identifier (e.g., `"seg-045"`) |

**Response `200`:**

```json
{
  "segment_id": "seg-045",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "segment_number": 45,
  "start_time": 1320,
  "end_time": 1350,
  "classification": "rejected",
  "sqi_values": {
    "kurtosis": 12.8,
    "skewness": 2.41,
    "snr": 4.2,
    "mean_hr": 68.1,
    "sdnn": 42.3,
    "rmssd": 38.1,
    "pnn50": 0.18,
    "lf_hf_ratio": 1.9
  },
  "failed_rules": [
    {
      "metric": "kurtosis",
      "value": 12.8,
      "threshold": 10.0,
      "operator": "max",
      "description": "Kurtosis exceeds maximum threshold — high-amplitude spike artifact suspected"
    },
    {
      "metric": "snr",
      "value": 4.2,
      "threshold": 8.0,
      "operator": "min",
      "description": "Signal-to-noise ratio below minimum threshold — poor signal quality"
    }
  ],
  "waveform_data": [0.012, 0.015, 0.019, 0.024, "...truncated..."]
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `404` | `segment_id` does not exist for this recording |

---

### POST /api/reports/generate

Trigger asynchronous generation of a quality report for a completed assessment. The canonical report is stored as JSON; HTML and PDF are rendered exports from that JSON payload.

**Request:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "format": "pdf",
  "include_waveform_plots": true
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recording_id` | string (UUID) | yes | Must reference a recording with `status = "completed"` |
| `format` | string | yes | `"json"`, `"html"`, or `"pdf"`; `"json"` returns the canonical payload |
| `include_waveform_plots` | boolean | no | Render per-segment waveform thumbnails; default `true` |

**Response `202`:**

```json
{
  "report_id": "r9f8e7d6-c5b4-3a21-0987-654321fedcba",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "generating",
  "format": "pdf"
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `400` | Recording assessment is not in `"completed"` status |
| `400` | `format` is not `"json"`, `"html"`, or `"pdf"` |

---

### GET /api/reports/{report_id}

Download or retrieve a generated report.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_id` | string (UUID) | Report identifier returned by `/api/reports/generate` |

**Response `200` — JSON format:**

```json
{
  "report_id": "r9f8e7d6-c5b4-3a21-0987-654321fedcba",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "format": "json",
  "generated_at": "2024-11-15T08:35:22Z",
  "content_json": {
    "summary": {},
    "timeline": [],
    "flagged_segments": [],
    "recommendations": [],
    "confidence": "high",
    "skipped_steps": [],
    "limitations": []
  }
}
```

**Response `200` — PDF export:**

- Content-Type: `application/pdf`
- Body: binary PDF file rendered from `content_json`
- Headers: `Content-Disposition: attachment; filename="quality-report-<recording_id>.pdf"`

**Response `200` — HTML export:**

```json
{
  "report_id": "r9f8e7d6-c5b4-3a21-0987-654321fedcba",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "format": "html",
  "generated_at": "2024-11-15T08:35:22Z",
  "content_html": "<html><body><h1>Quality Assessment Report</h1>...</body></html>"
}
```

**Response `200` — still generating:**

```json
{
  "report_id": "r9f8e7d6-c5b4-3a21-0987-654321fedcba",
  "status": "generating"
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `report_id` does not exist |
| `500` | Report generation failed |

---

### GET /api/dashboard/summary

Retrieve high-level summary statistics for the dashboard home view.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | no | Lookback window in days; default `30` |
| `signal_type` | string | no | Filter by `"ecg"` or `"ppg"`; omit for all |

**Response `200`:**

```json
{
  "total_recordings": 148,
  "period_days": 30,
  "recent_assessments": [
    {
      "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "subject_id": "SUBJ-042",
      "signal_type": "ecg",
      "assessed_at": "2024-11-15T08:33:05Z",
      "acceptance_rate": 0.817,
      "verdict": "acceptable"
    },
    {
      "recording_id": "c3d2e1f0-a9b8-7654-3210-abcdef012345",
      "subject_id": "SUBJ-031",
      "signal_type": "ppg",
      "assessed_at": "2024-11-14T14:10:00Z",
      "acceptance_rate": 0.312,
      "verdict": "poor"
    }
  ],
  "quality_trends": [
    { "date": "2024-11-09", "mean_acceptance_rate": 0.85, "assessments_count": 5 },
    { "date": "2024-11-10", "mean_acceptance_rate": 0.81, "assessments_count": 7 },
    { "date": "2024-11-15", "mean_acceptance_rate": 0.76, "assessments_count": 4 }
  ],
  "alerts": [
    {
      "alert_id": "alert-001",
      "type": "low_quality",
      "severity": "high",
      "recording_id": "c3d2e1f0-a9b8-7654-3210-abcdef012345",
      "message": "Recording SUBJ-031 PPG has acceptance rate of 31.2% — flagged for human review.",
      "created_at": "2024-11-14T14:10:15Z",
      "acknowledged": false
    }
  ]
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `400` | `days` is zero or negative |
| `500` | Database query failure |

---

### GET /api/dashboard/timeline/{recording_id}

Retrieve per-segment quality timeline data for the waveform monitoring view.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | string (UUID) | Recording identifier |

**Response `200`:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "signal_type": "ecg",
  "total_segments": 120,
  "segment_duration_seconds": 30,
  "timeline": [
    {
      "segment_number": 1,
      "start_time": 0,
      "end_time": 30,
      "classification": "accepted",
      "quality_score": 0.91
    },
    {
      "segment_number": 45,
      "start_time": 1320,
      "end_time": 1350,
      "classification": "rejected",
      "quality_score": 0.23
    },
    {
      "segment_number": 120,
      "start_time": 3570,
      "end_time": 3600,
      "classification": "accepted",
      "quality_score": 0.87
    }
  ]
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `400` | Assessment not yet completed for this recording |

---

### GET /api/recordings/{recording_id}/waveform

Retrieve raw or downsampled waveform signal data for visualization.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start` | float | No | Start time in seconds (default: 0) |
| `end` | float | No | End time in seconds (default: full duration) |
| `downsample` | integer | No | Target number of points (default: 10000). Raw data returned if omitted or if raw length < target. |

**Response (200):**

```json
{
  "recording_id": "abc-123",
  "signal_type": "ecg",
  "sampling_rate": 500,
  "start_time": 0.0,
  "end_time": 60.0,
  "channels": [
    {
      "name": "Lead II",
      "data": [0.12, 0.15, 0.18, -0.02, "..."]
    }
  ],
  "downsampled": true,
  "original_length": 30000,
  "returned_length": 10000
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `400` | `start` is greater than or equal to `end` |
| `400` | Assessment not yet completed for this recording |

---

### POST /api/chat

Submit a natural-language question about a recording to the agent chatbot.

**Request:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "Why was segment 45 rejected?"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recording_id` | string (UUID) | yes | Context recording for the question |
| `message` | string | yes | Natural-language question from the researcher or clinician |
| `conversation_id` | string | no | For multi-turn conversations; omit for new conversation |

**Response `200`:**

```json
{
  "conversation_id": "conv-abc123",
  "response": "Segment 45 (t=1320s to t=1350s) was rejected because two SQI metrics fell outside acceptable thresholds: kurtosis was 12.8 (maximum allowed: 10.0), indicating a high-amplitude spike artifact, and SNR was 4.2 (minimum required: 8.0), indicating a poor signal-to-noise ratio. Both failures are consistent with motion artifact — the patient may have moved during this window. The surrounding segments (44 and 46) were accepted with normal SQI values.",
  "sources": [
    {
      "type": "segment_detail",
      "segment_id": "seg-045",
      "segment_number": 45
    },
    {
      "type": "rule_evaluation",
      "metrics_cited": ["kurtosis", "snr"]
    }
  ]
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist or assessment not completed |
| `400` | `message` is empty |
| `500` | LLM inference failure |

---

### GET /api/agent/logs/{recording_id}

Retrieve the full agent decision log for a recording. Used for transparency, debugging, and clinical audit.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | string (UUID) | Recording identifier |

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stage` | string | no | Filter by stage name (e.g., `"assessing"`) |
| `tool` | string | no | Filter by tool name (e.g., `"compute_sqi_windowed"`) |

**Response `200`:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "total_steps": 12,
  "logs": [
    {
      "step": 1,
      "timestamp": "2024-11-15T08:32:15Z",
      "stage": "initialized",
      "tool_called": null,
      "input_summary": null,
      "output_summary": null,
      "reasoning": "Received recording f47ac10b. Signal type: ECG. Sampling rate: 500 Hz. File format: EDF. No preprocessing flag set — proceeding directly to full ECG pipeline.",
      "duration_ms": null,
      "success": true
    },
    {
      "step": 2,
      "timestamp": "2024-11-15T08:32:15Z",
      "stage": "assessing",
      "tool_called": "compute_sqi_windowed",
      "input_summary": "signal=<loaded waveform>, fs=500, signal_type=ecg, window_sec=30",
      "output_summary": "120 windows processed. 98 passed quality threshold, 22 flagged. Acceptance rate: 81.7%.",
      "reasoning": "Signal type is ECG. Calling compute_sqi_windowed with 30s windows to produce segment-level quality scores for timeline classification.",
      "duration_ms": 38420,
      "success": true
    },
    {
      "step": 3,
      "timestamp": "2024-11-15T08:32:54Z",
      "stage": "interpreting",
      "tool_called": null,
      "input_summary": null,
      "output_summary": null,
      "reasoning": "Acceptance rate of 81.7% is above the 40% escalation threshold. Rejected segments 45–50 are consecutive, suggesting a localized artifact event rather than systematic device failure. No escalation required. Proceeding to report generation.",
      "duration_ms": null,
      "success": true
    }
  ]
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `404` | No agent logs exist for this recording (assessment not started) |

---

### PUT /api/settings/thresholds

Update the default SQI classification thresholds used when no `rule_dict` is provided in `/api/assess`.

**Request:**

```json
{
  "thresholds": {
    "mean_hr":    { "min": 40,    "max": 200   },
    "sdnn":       { "min": 7.93,  "max": 676   },
    "rmssd":      { "min": 5.0,   "max": 300   },
    "pnn50":      { "min": 0.0,   "max": 1.0   },
    "kurtosis":   { "min": -1.5,  "max": 10.0  },
    "skewness":   { "min": -3.0,  "max": 3.0   },
    "snr":        { "min": 8.0,   "max": null  },
    "lf_hf_ratio":{ "min": 0.2,   "max": 5.0  }
  }
}
```

**Fields:**

Each key in `thresholds` is a metric name. Each value is an object with optional `min` and/or `max` fields (both accept `null` to indicate "no bound on this side").

**Response `200`:**

```json
{
  "status": "updated",
  "updated_at": "2024-11-15T09:00:00Z",
  "updated_by": "admin",
  "metrics_updated": [
    "mean_hr", "sdnn", "rmssd", "pnn50",
    "kurtosis", "skewness", "snr", "lf_hf_ratio"
  ]
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `400` | A metric name is not recognized |
| `400` | `min` is greater than `max` for any metric |
| `400` | `thresholds` object is empty |
| `500` | Settings persistence failure |
