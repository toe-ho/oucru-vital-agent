# 04 — User Personas

[← Back to Index](../00-index.md)

---

## Overview

Three user personas represent the primary audiences for the system. Design and prioritisation decisions should be evaluated against all three, with the primary persona (Clinical Researcher) taking precedence in cases of conflict.

| # | Persona | Role | Priority |
|---|---------|------|----------|
| 1 | The Clinical Researcher | Reviews waveform data quality daily | Primary |
| 2 | The Data Engineer | Maintains pipeline and system configuration | Secondary |
| 3 | The Study Coordinator | Consumes quality reports for compliance | Tertiary |

---

## Persona 1 — The Clinical Researcher

**Priority:** Primary

| Field | Detail |
|-------|--------|
| Role | Clinical Researcher at OUCRU |
| Technical comfort | Moderate — comfortable with clinical software, EDC systems, and spreadsheets; not a programmer |

### Goals

- Quickly assess the quality of waveform recordings collected from study participants before including them in analysis
- Understand *why* a recording was flagged as poor quality, not just that it was
- Reduce time spent on manual data quality review so more time is available for actual research
- Trust the system's assessments enough to act on them without needing to manually verify every result

### Frustrations

- Spending hours manually reviewing waveform plots to identify noise segments and artifacts
- Receiving vague quality flags ("signal poor") with no explanation of what caused the issue or where in the recording it occurred
- Discovering quality problems late — days after data collection — when it is too late to repeat the recording
- Quality review tools that require programming knowledge or command-line interaction

### Typical Workflow

1. Downloads a batch of waveform files from the EDC system at the end of a study day
2. Uploads files to the quality monitoring system via the web dashboard
3. Waits for assessment results (expects results within minutes, not hours)
4. Reviews quality scores and segment-level annotations for each recording
5. Makes include/exclude decisions for downstream analysis
6. Downloads a quality report to attach to the study data package

### Key Dashboard Needs

- Simple drag-and-drop file upload
- Clear visual quality score per recording (e.g., traffic-light indicator)
- Segment-level issue annotations with plain-language descriptions
- One-click report download

---

## Persona 2 — The Data Engineer

**Priority:** Secondary

| Field | Detail |
|-------|--------|
| Role | Data Engineer, OUCRU Data Management Team |
| Technical comfort | High — proficient in Python, SQL, Linux, cloud infrastructure; builds and maintains data pipelines |

### Goals

- Configure and maintain the quality monitoring system with minimal friction
- Monitor system health: job queue status, processing errors, throughput metrics
- Adjust quality check parameters (thresholds, enabled checks, device-specific settings) without redeploying the application
- Integrate the quality monitoring system with the existing EDC data pipeline via API
- Diagnose and resolve issues quickly when assessments fail or produce unexpected results

### Frustrations

- Existing QC tooling requires manual per-device rule authoring that is tedious to maintain as new devices are onboarded
- No centralised visibility into which recordings are queued, processing, or failed
- Quality issues only surface during manual review rather than being caught automatically at ingestion
- Lack of programmatic API access to quality results — must export data manually for downstream pipeline integration

### Typical Workflow

1. Configures device profiles and quality check parameters via a configuration file or admin interface
2. Monitors the job queue and system logs via the dashboard or API
3. Investigates failed jobs by reviewing agent logs and error messages
4. Calls the REST API to retrieve quality assessment results for integration with downstream analysis pipelines
5. Updates system configuration when new device types are onboarded

### Key System Needs

- Well-documented REST API with OpenAPI/Swagger specification
- Configurable quality check parameters per device type
- Structured logging and error reporting for failed jobs
- Admin view in dashboard showing queue depth, throughput, and error rates

---

## Persona 3 — The Study Coordinator

*(Team-inferred persona — not explicitly specified in original requirements but included based on clinical research workflow analysis)*

**Priority:** Tertiary

| Field | Detail |
|-------|--------|
| Role | Study Coordinator, Clinical Trial Office |
| Technical comfort | Low — comfortable with email, standard office software, and web portals; does not use clinical data tools directly |

### Goals

- Receive clear, timely quality summary reports for ongoing studies to satisfy regulatory and sponsor reporting requirements
- Understand overall data quality trends across a study without needing to interpret raw signal data
- Export reports in formats compatible with regulatory submission packages (PDF)
- Be notified when data quality falls below acceptable thresholds so corrective action can be taken promptly

### Frustrations

- Quality reports are currently compiled manually by data engineers, causing delays of days to weeks
- Reports are inconsistently formatted across study periods, making it difficult to compare quality across time
- Has no self-service access to quality data — must request reports from the data team and wait
- Report language is often too technical; clinical significance of quality issues is not explained

### Typical Workflow

1. Receives an automated notification (email or dashboard alert) that a quality report is ready
2. Logs into the dashboard to view the summary report for a study
3. Reviews overall pass/fail rates, trend charts, and flagged sessions
4. Downloads the PDF report to attach to regulatory submission or share with the study sponsor
5. Escalates critical quality issues to the data team or site principal investigator

### Key Report Needs

- Executive summary section with plain-language interpretation of quality results
- Overall quality score and pass/fail rate per study session
- Trend visualisation across time (quality degradation or improvement)
- Professional PDF format suitable for regulatory submission
- Automated delivery — no manual request required
