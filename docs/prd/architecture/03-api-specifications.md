# 03 — API Specifications

[← Back to Index](../00-index.md)

---

## Overview

**Scope:** All endpoints handle waveform data (ECG, PPG) only. Imaging support is deferred to future phases.

All endpoints are served by the FastAPI backend at base URL `/api`. Request and response bodies use `application/json` unless noted. File uploads use `multipart/form-data`.

Uploaded files must already be de-identified before upload. The backend stores waveform files and derived outputs, but the agent must not send raw waveform arrays to the LLM; prompts should contain metadata, tool outputs, SQI summaries, and report/chat context only.

---

## Authentication and Authorization

All endpoints except health checks require a valid JWT bearer token issued after Google OAuth sign-in.

| Role | Capabilities |
|------|--------------|
| `admin` | Manage users, roles, settings, and all records |
| `researcher` | Upload recordings, start assessments, view results, generate reports, use chat |
| `reviewer` | View assigned recordings, reports, logs, and use chat |
| `readonly` | View accessible recordings and reports only |

Endpoints that modify system-wide settings require `admin`. Assessment, report, and chat endpoints require access to the target recording or assessment job.

### GET /api/auth/me

Return the authenticated user and role list.

**Response `200`:**

```json
{
  "user_id": "9f3b4a7e-49f8-4b31-ae32-2f17f97d7f2a",
  "email": "researcher@example.org",
  "full_name": "OUCRU Researcher",
  "roles": ["researcher"]
}
```

---

## Standard Error Response

All error responses share this structure:

```json
{
  "error": "NotFound",
  "detail": "Recording with id 'abc123' does not exist.",
  "request_id": "req-20241115-083211"
}
```

### HTTP Status Codes Used

| Code | Meaning |
|------|---------|
| `200` | Success — resource returned or action completed |
| `201` | Created — new resource created |
| `202` | Accepted — request accepted for asynchronous processing |
| `400` | Bad Request — invalid parameters or malformed body |
| `401` | Unauthorized — missing or invalid JWT |
| `403` | Forbidden — authenticated user lacks required role/access |
| `404` | Not Found — resource does not exist |
| `422` | Unprocessable Entity — FastAPI validation error |
| `500` | Internal Server Error — unexpected backend or agent failure |

---

## Status and Classification Enums

| Entity | Field | Values |
|--------|-------|--------|
| Recording | `status` | `uploaded`, `processing`, `completed`, `failed`, `deleted` |
| Assessment job | `status` | `queued`, `processing`, `completed`, `failed`, `cancelled` |
| Segment | `classification` | `accept`, `reject`, `pending`, `uncomputable` |
| Report | `status` | `generating`, `completed`, `failed` |

---

## Endpoints

---

### POST /api/upload

Upload a de-identified waveform file and register it as a new recording.

**Authorization:** `admin` or `researcher`

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | yes | EDF, MIT/WFDB bundle, CSV, or Parquet waveform file |
| `signal_type` | string | yes | `"ecg"` or `"ppg"` |
| `sampling_rate` | number | yes | Samples per second, e.g. `500` |
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
    "file_format": "edf",
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
| `400` | Unsupported file format |
| `400` | `signal_type` is not `"ecg"` or `"ppg"` |
| `400` | `sampling_rate` is zero or negative |
| `500` | File storage write failure |

---

### GET /api/recordings

List recordings visible to the authenticated user.

**Authorization:** any authenticated role with recording access

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `signal_type` | string | no | Filter by `"ecg"` or `"ppg"` |
| `status` | string | no | Filter by recording status |
| `limit` | integer | no | Page size; default `50` |
| `offset` | integer | no | Page offset; default `0` |

**Response `200`:**

```json
{
  "items": [
    {
      "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "filename": "subject_042_ecg_2024-11-15.edf",
      "signal_type": "ecg",
      "status": "completed",
      "uploaded_at": "2024-11-15T08:32:11Z",
      "latest_assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "latest_verdict": "acceptable"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

### GET /api/recordings/{recording_id}

Retrieve recording metadata and latest assessment summary.

**Authorization:** any authenticated role with recording access

**Response `200`:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "filename": "subject_042_ecg_2024-11-15.edf",
  "signal_type": "ecg",
  "sampling_rate": 500,
  "file_format": "edf",
  "duration_seconds": 3600,
  "status": "completed",
  "latest_assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### POST /api/assess

Trigger a quality assessment for an uploaded recording. The assessment runs asynchronously and creates an `assessment_jobs` row.

**Authorization:** `admin` or `researcher`

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
      "mean_hr": { "min": 40, "max": 200 },
      "sdnn": { "min": 7.93, "max": 676 },
      "kurtosis": { "min": -1.5, "max": 10.0 }
    }
  }
}
```

**Response `202`:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "queued",
  "estimated_duration_seconds": 45
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `recording_id` does not exist |
| `400` | Recording status is not eligible for assessment |
| `400` | `segment_duration` is zero or negative |
| `400` | `overlap` is not in range `[0.0, 1.0)` |

---

### GET /api/assessment-jobs/{assessment_job_id}

Retrieve assessment job status and progress. Poll this endpoint while processing.

**Authorization:** any authenticated role with access to the job's recording

**Response `200` — processing:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "processing",
  "progress": {
    "current_stage": "assessing",
    "segments_processed": 60,
    "total_segments": 120,
    "progress_pct": 50.0
  }
}
```

**Response `200` — completed:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "started_at": "2024-11-15T08:32:15Z",
  "completed_at": "2024-11-15T08:33:05Z",
  "total_segments": 120,
  "processed_segments": 120
}
```

---

### GET /api/assessment-jobs/{assessment_job_id}/results

Retrieve completed assessment results for one job.

**Authorization:** any authenticated role with access to the job's recording

**Response `200`:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "signal_type": "ecg",
  "assessed_at": "2024-11-15T08:33:05Z",
  "summary": {
    "total_segments": 120,
    "accepted": 98,
    "rejected": 22,
    "uncomputable": 0,
    "acceptance_rate": 0.817,
    "overall_quality_score": 0.79,
    "verdict": "acceptable"
  },
  "segments": [
    {
      "segment_id": "650e8400-e29b-41d4-a716-446655440001",
      "segment_number": 1,
      "start_time": 0,
      "end_time": 30,
      "classification": "accept",
      "quality_score": 0.91,
      "sqi_summary": {
        "kurtosis": 3.14,
        "skewness": 0.12,
        "snr": 18.7,
        "mean_hr": 72.3
      }
    },
    {
      "segment_id": "650e8400-e29b-41d4-a716-446655440045",
      "segment_number": 45,
      "start_time": 1320,
      "end_time": 1350,
      "classification": "reject",
      "quality_score": 0.23,
      "sqi_summary": {
        "kurtosis": 12.8,
        "skewness": 2.41,
        "snr": 4.2,
        "mean_hr": 68.1
      }
    }
  ],
  "agent_interpretation": "The recording shows good overall quality with an acceptance rate of 81.7%. A cluster of rejected segments was observed between t=1320s and t=1500s, likely attributable to motion artifact.",
  "escalated": false
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `assessment_job_id` does not exist |
| `400` | Assessment is not completed |
| `500` | Assessment failed internally |

---

### GET /api/assessment-jobs/{assessment_job_id}/segments/{segment_id}

Retrieve the full SQI breakdown for one segment. Use `/api/recordings/{recording_id}/waveform` with the segment time range to fetch waveform samples.

**Authorization:** any authenticated role with access to the job's recording

**Response `200`:**

```json
{
  "segment_id": "650e8400-e29b-41d4-a716-446655440045",
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "segment_number": 45,
  "start_time": 1320,
  "end_time": 1350,
  "classification": "reject",
  "quality_score": 0.23,
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
  ]
}
```

---

### GET /api/recordings/{recording_id}/waveform

Retrieve raw or downsampled waveform signal data for visualization.

**Authorization:** any authenticated role with recording access

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start` | float | no | Start time in seconds; default `0` |
| `end` | float | no | End time in seconds; default full duration |
| `downsample` | integer | no | Target number of points; default `10000` |

**Response `200`:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "signal_type": "ecg",
  "sampling_rate": 500,
  "start_time": 0.0,
  "end_time": 60.0,
  "channels": [
    {
      "name": "Lead II",
      "data": [0.12, 0.15, 0.18, -0.02]
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
| `400` | `downsample` is zero or negative |

---

### POST /api/reports/generate

Trigger asynchronous generation of a quality report for a completed assessment job. The canonical report is stored as JSON; HTML and PDF are rendered exports from that JSON payload on the `reports` row.

**Authorization:** `admin` or `researcher`

**Request:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "format": "pdf",
  "include_waveform_plots": true
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assessment_job_id` | string (UUID) | yes | Must reference a completed assessment job |
| `format` | string | yes | `"json"`, `"html"`, or `"pdf"` |
| `include_waveform_plots` | boolean | no | Render per-segment waveform thumbnails; default `true` |

**Response `202`:**

```json
{
  "report_id": "r9f8e7d6-c5b4-3a21-0987-654321fedcba",
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "generating",
  "format": "pdf"
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| `404` | `assessment_job_id` does not exist |
| `400` | Assessment job is not `"completed"` |
| `400` | `format` is not `"json"`, `"html"`, or `"pdf"` |

---

### GET /api/reports/{report_id}

Download or retrieve a generated report.

**Authorization:** any authenticated role with access to the report's recording

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `format` | string | no | `"json"`, `"html"`, or `"pdf"`; defaults to stored report format |

**Response `200` — JSON format:**

```json
{
  "report_id": "r9f8e7d6-c5b4-3a21-0987-654321fedcba",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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

---

### GET /api/dashboard/summary

Retrieve high-level summary statistics for the dashboard home view.

**Authorization:** any authenticated role with dashboard access

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | no | Lookback window in days; default `30` |
| `signal_type` | string | no | Filter by `"ecg"` or `"ppg"` |

**Response `200`:**

```json
{
  "total_recordings": 148,
  "period_days": 30,
  "recent_assessments": [
    {
      "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "subject_id": "SUBJ-042",
      "signal_type": "ecg",
      "assessed_at": "2024-11-15T08:33:05Z",
      "acceptance_rate": 0.817,
      "verdict": "acceptable"
    }
  ],
  "quality_trends": [
    { "date": "2024-11-09", "mean_acceptance_rate": 0.85, "assessments_count": 5 }
  ],
  "alerts": [
    {
      "alert_id": "alert-001",
      "type": "low_quality",
      "severity": "high",
      "recording_id": "c3d2e1f0-a9b8-7654-3210-abcdef012345",
      "assessment_job_id": "d4e3f2a1-b0c9-8765-4321-fedcba987654",
      "message": "Recording SUBJ-031 PPG has acceptance rate of 31.2% — flagged for human review.",
      "created_at": "2024-11-14T14:10:15Z",
      "acknowledged": false
    }
  ]
}
```

---

### GET /api/dashboard/timeline/{assessment_job_id}

Retrieve per-segment quality timeline data for the waveform monitoring view.

**Authorization:** any authenticated role with access to the job's recording

**Response `200`:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "signal_type": "ecg",
  "total_segments": 120,
  "segment_duration_seconds": 30,
  "timeline": [
    {
      "segment_number": 1,
      "start_time": 0,
      "end_time": 30,
      "classification": "accept",
      "quality_score": 0.91
    },
    {
      "segment_number": 45,
      "start_time": 1320,
      "end_time": 1350,
      "classification": "reject",
      "quality_score": 0.23
    }
  ]
}
```

---

### POST /api/conversations

Create a conversation grounded in a recording, assessment job, and optionally a report.

**Authorization:** `admin`, `researcher`, or `reviewer` with access to the target recording

**Request:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "report_id": null,
  "title": "Segment quality discussion"
}
```

**Response `201`:**

```json
{
  "conversation_id": "0f24d1fb-8817-4b68-8e6e-76af5d2df4b1",
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Segment quality discussion",
  "created_at": "2024-11-15T08:40:00Z"
}
```

---

### GET /api/conversations/{conversation_id}/messages

Retrieve chat history for a conversation.

**Authorization:** any authenticated role with access to the conversation's recording

**Response `200`:**

```json
{
  "conversation_id": "0f24d1fb-8817-4b68-8e6e-76af5d2df4b1",
  "messages": [
    {
      "message_id": "5d7a0e97-5ec5-41b6-859c-93d29b4a84b6",
      "role": "user",
      "content": "Why was segment 45 rejected?",
      "created_at": "2024-11-15T08:41:00Z"
    },
    {
      "message_id": "6f3c4865-391d-4f20-9316-d5e73c5779f1",
      "role": "assistant",
      "content": "Segment 45 was rejected because kurtosis and SNR fell outside configured thresholds.",
      "sources": [
        { "type": "segment_detail", "segment_id": "650e8400-e29b-41d4-a716-446655440045" }
      ],
      "created_at": "2024-11-15T08:41:02Z"
    }
  ]
}
```

---

### POST /api/conversations/{conversation_id}/messages

Submit a natural-language question about a recording or assessment job to the agent chatbot.

**Authorization:** `admin`, `researcher`, or `reviewer` with access to the conversation's recording

**Request:**

```json
{
  "message": "Why was segment 45 rejected?"
}
```

**Response `200`:**

```json
{
  "conversation_id": "0f24d1fb-8817-4b68-8e6e-76af5d2df4b1",
  "user_message_id": "5d7a0e97-5ec5-41b6-859c-93d29b4a84b6",
  "assistant_message_id": "6f3c4865-391d-4f20-9316-d5e73c5779f1",
  "response": "Segment 45 (t=1320s to t=1350s) was rejected because two SQI metrics fell outside acceptable thresholds: kurtosis was 12.8 (maximum allowed: 10.0), and SNR was 4.2 (minimum required: 8.0).",
  "sources": [
    {
      "type": "segment_detail",
      "segment_id": "650e8400-e29b-41d4-a716-446655440045",
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
| `404` | `conversation_id` does not exist |
| `400` | `message` is empty |
| `500` | LLM inference failure |

---

### POST /api/chat

MVP convenience endpoint for one-shot or multi-turn chat. If `conversation_id` is omitted, the backend creates a conversation before storing `chat_messages` rows.

**Authorization:** `admin`, `researcher`, or `reviewer` with access to the target recording

**Request:**

```json
{
  "recording_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "conversation_id": null,
  "message": "Why was segment 45 rejected?"
}
```

**Response `200`:** same as `POST /api/conversations/{conversation_id}/messages`.

---

### GET /api/assessment-jobs/{assessment_job_id}/logs

Retrieve the full agent decision log for an assessment job.

**Authorization:** any authenticated role with access to the job's recording

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `stage` | string | no | Filter by stage name, e.g. `"assessing"` |
| `tool` | string | no | Filter by tool name, e.g. `"compute_sqi_windowed"` |

**Response `200`:**

```json
{
  "assessment_job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
      "reasoning": "Received recording f47ac10b. Signal type: ECG. Sampling rate: 500 Hz. File format: EDF.",
      "duration_ms": null,
      "success": true
    },
    {
      "step": 2,
      "timestamp": "2024-11-15T08:32:15Z",
      "stage": "assessing",
      "tool_called": "compute_sqi_windowed",
      "input_summary": "signal=<loaded waveform>, fs=500, signal_type=ecg, window_sec=30",
      "output_summary": "120 windows processed. 98 accepted, 22 rejected. Acceptance rate: 81.7%.",
      "reasoning": "Signal type is ECG. Calling compute_sqi_windowed with 30s windows to produce segment-level quality scores.",
      "duration_ms": 38420,
      "success": true
    }
  ]
}
```

---

### GET /api/settings/thresholds

Retrieve current default SQI classification thresholds.

**Authorization:** any authenticated role

**Response `200`:**

```json
{
  "thresholds": {
    "mean_hr": { "min": 40, "max": 200 },
    "sdnn": { "min": 7.93, "max": 676 },
    "rmssd": { "min": 5.0, "max": 300 },
    "pnn50": { "min": 0.0, "max": 1.0 },
    "kurtosis": { "min": -1.5, "max": 10.0 },
    "skewness": { "min": -3.0, "max": 3.0 },
    "snr": { "min": 8.0, "max": null },
    "lf_hf_ratio": { "min": 0.2, "max": 5.0 }
  },
  "updated_at": "2024-11-15T09:00:00Z"
}
```

---

### PUT /api/settings/thresholds

Update the default SQI classification thresholds used when no `rule_dict` is provided in `/api/assess`.

**Authorization:** `admin`

**Request:**

```json
{
  "thresholds": {
    "mean_hr": { "min": 40, "max": 200 },
    "sdnn": { "min": 7.93, "max": 676 },
    "rmssd": { "min": 5.0, "max": 300 },
    "pnn50": { "min": 0.0, "max": 1.0 },
    "kurtosis": { "min": -1.5, "max": 10.0 },
    "skewness": { "min": -3.0, "max": 3.0 },
    "snr": { "min": 8.0, "max": null },
    "lf_hf_ratio": { "min": 0.2, "max": 5.0 }
  }
}
```

**Response `200`:**

```json
{
  "status": "updated",
  "updated_at": "2024-11-15T09:00:00Z",
  "updated_by": "9f3b4a7e-49f8-4b31-ae32-2f17f97d7f2a",
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
| `403` | Authenticated user is not an admin |
| `500` | Settings persistence failure |
