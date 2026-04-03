# 03 — Goals and Non-Goals

[← Back to Index](00-index.md)

---

## Goals

### G1 — Automate End-to-End Data Quality Monitoring

Deliver a system that takes a waveform data file as input and produces a structured quality assessment as output, with no manual steps in between. The pipeline covers: file upload → signal parsing → agent-orchestrated quality checks → classification → result storage.

**Success criterion:** A practitioner uploads a file via the dashboard and receives a quality assessment without any manual configuration or intervention.

---

### G2 — Automate Quality Report Generation

Generate structured quality reports automatically upon completion of each assessment run. Reports must be produced without manual compilation by data engineers or clinical staff.

**Success criterion:** A downloadable report (PDF and/or JSON) is available within the dashboard within a defined time window after upload completes. Zero manual steps required post-upload.

---

### G3 — Intelligent Problem Diagnosis

The agent must go beyond binary pass/fail classification. It must identify and characterise specific quality issue types within a recording:

- Transient noise segments (patient movement, electrical interference)
- Sensor disconnection events
- Missing data windows
- Signal baseline drift
- Sampling irregularities

**Success criterion:** Quality reports include segment-level annotations identifying issue type, location (timestamp range), and severity.

---

### G4 — Web-Based Dashboard for Medical Practitioners

Provide a web interface accessible to non-technical clinical staff. The dashboard must support:

- File upload and job submission
- Real-time or near-real-time status monitoring
- Quality result visualisation (signal quality scores, issue annotations)
- Report download

**Success criterion:** A clinical researcher with no programming background can upload a file, monitor progress, and download a report without assistance.

---

### G5 — Measurable Performance Improvement

Achieve quantifiable improvements over the current baseline:

| Metric | Target |
|--------|--------|
| Reporting time | ≥ 50% reduction vs. manual baseline |
| Defect detection precision | ≥ 20% improvement vs. static rule baseline |
| Defect detection recall | ≥ 20% improvement vs. static rule baseline |

---

### G6 — Chatbot Interface

Provide a natural language conversational interface allowing practitioners to query quality assessment results using plain English. Example queries:

```
"Why was segment 45 rejected?"
"What is the average SSQI for today's recordings?"
"How many recordings failed quality checks this week?"
```

The chatbot shall also explain configuration options, translate SQI metric names into clinically meaningful language, and assist users in understanding quality reports.

**Success criterion:** A practitioner can ask a natural language question about any quality result and receive a meaningful, accurate answer without navigating technical dashboards.

---

### G7 — Token-Encoding Privacy Layer

Implement a preprocessing layer that anonymises or encodes waveform metadata and clinical context tokens before they are included in any prompt sent to an external LLM API. This is a security best practice to mitigate privacy risk when using hosted LLM endpoints.

Implementation approach: Reversible token substitution map applied at the agent's prompt-construction layer; decoded on response receipt. Encoding strategy shall be configurable per deployment and documented with its privacy guarantees and information loss characteristics.

**Success criterion:** All prompts sent to external LLM APIs pass through the encoding layer with no raw metadata tokens exposed; decoded responses are functionally equivalent to unencoded responses.

---

## Non-Goals

> The following are explicitly out of scope for this project. These boundaries exist to keep the project focused and deliverable within the capstone timeline and budget.

### NG1 — No New Signal Processing Algorithms

The team will **not** design, train, or deploy new machine learning models or signal processing algorithms for waveform quality detection. All signal assessment logic is provided by the `vital_sqi` library. The agent's role is orchestration and reasoning, not signal processing.

### NG2 — No Replacement of `vital_sqi`

The project will **not** reimplement or fork `vital_sqi` functionality. The library is treated as a fixed, trusted dependency. Contributions to `vital_sqi` itself are out of scope.

### NG3 — No Real-Time Streaming

The initial system operates on **offline recordings** — files already collected and stored. Real-time streaming ingestion from live devices is not in scope for this phase.

### NG4 — No Mobile Application

The user interface is a web dashboard only. No iOS or Android application will be built.

### NG5 — No Patient-Identifiable Information (PII)

The system will **not** handle, store, or process patient-identifiable information. Input files are assumed to be de-identified prior to upload. The system provides no PII management, access control for sensitive records, or HIPAA/GDPR compliance infrastructure beyond what is standard for the GCP deployment environment.

### NG6 — Imaging Data Quality Assessment

**NG6 — Imaging Data Quality Assessment:** OUCRU's Objective 1 references both imaging and waveform data. Imaging quality monitoring is explicitly deferred to future phases. This project focuses exclusively on waveform data (ECG, PPG). | Imaging requires different processing pipelines and assessment methods; waveform-first approach allows focused delivery.

