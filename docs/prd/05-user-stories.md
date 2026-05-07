# 05 — User Stories

[← Back to Index](00-index.md)

---

## Overview

This document captures the user stories for the **Agentic AI for High-Frequency Data Quality Monitoring** system at OUCRU. Stories are derived from three primary personas and cover all critical workflows from data ingestion through agentic processing, reporting, and chatbot interactions.

---

## Personas

| Persona | Role | Technical Level | Primary Goal |
|---|---|---|---|
| **Clinical Researcher** | Primary user; owns study data, interprets quality results | Low–Medium | Ensure collected ECG/PPG data meets quality thresholds for publication |
| **Data Engineer** | Secondary; configures pipelines, integrates vital_sqi, maintains system | High | Keep pipeline reliable, performant, and configurable |
| **Study Coordinator** | Tertiary; schedules recordings, tracks data collection progress | Low | Track overall study data quality without deep technical knowledge |

---

## User Stories

| ID | Persona | Story | Priority |
|---|---|---|---|
| US-001 | Clinical Researcher | As a Clinical Researcher, I want to upload ECG and PPG recording files (EDF, MIT/WFDB, CSV) through a web interface so that the system can automatically begin quality assessment without manual command-line intervention. | Must |
| US-002 | Clinical Researcher | As a Clinical Researcher, I want to view the waveform of a recording with color-coded segment overlays (green = accepted, red = rejected) so that I can immediately see which portions of the signal are usable. | Must |
| US-003 | Study Coordinator | As a Study Coordinator, I want to view a quality dashboard that shows overall quality scores, accept/reject ratios, and trend charts across all submitted recordings so that I can track data collection progress at the study level. | Must |
| US-004 | Clinical Researcher | As a Clinical Researcher, I want to receive alerts when a recording's quality falls below a configured threshold so that I can take corrective action (e.g., request a re-recording) before the patient leaves the clinic. | Must |
| US-005 | Clinical Researcher | As a Clinical Researcher, I want to generate and download a quality report (PDF or HTML) for a specific recording so that I can share results with co-investigators and include them in study documentation. | Must |
| US-006 | Data Engineer | As a Data Engineer, I want to configure SQI thresholds, segmentation duration, overlap, and metric selection through a settings interface so that the pipeline can be tuned per study protocol without code changes. | Must |
| US-007 | Clinical Researcher | As a Clinical Researcher, I want to click on a rejected segment and see a detailed breakdown — which SQI metrics failed, their measured values, and the configured thresholds — so that I understand the clinical reason for rejection. | Must |
| US-008 | Data Engineer | As a Data Engineer, I want to submit multiple recording files in a single batch upload so that I can process an entire day's worth of patient data without uploading files one by one. | Must |
| US-009 | Clinical Researcher | As a Clinical Researcher, I want to view the AI agent's decision log — every tool call, reasoning step, and intermediate result — so that I can audit what the agent did and trust the output. | Must |
| US-010 | Clinical Researcher | As a Clinical Researcher, I want to compare quality metrics across multiple recordings side-by-side (e.g., Patient A vs. Patient B, or Day 1 vs. Day 3) so that I can identify systematic collection problems or patient-level trends. | Should |
| US-011 | Clinical Researcher | As a Clinical Researcher, I want to ask the system in natural language — e.g., "Why was segment 45 rejected?" or "What is the average SSQI for today's recordings?" — so that I can get answers without navigating technical dashboards. | Should |
| US-012 | Study Coordinator | As a Study Coordinator, I want to export a structured quality report in a regulatory-compliant format so that I can submit it to ethics committees or data monitoring boards as evidence of data integrity. | Must |
| US-013 | Data Engineer | As a Data Engineer, I want to receive meaningful error messages when a file upload fails due to an unsupported format, corrupted data, or missing sampling rate metadata so that I can diagnose and fix the issue quickly. | Must |
| US-014 | Study Coordinator | As a Study Coordinator, I want the dashboard to load within 3 seconds even when displaying results for 50+ recordings so that the interface remains usable during busy clinic days. | Should |
| US-015 | Clinical Researcher | As a Clinical Researcher, I want waveform and SQI data to be protected in transit and at rest so that anonymous waveform data is stored securely, consistent with OUCRU's relaxed privacy requirements for non-PII data. | Must |

---

## Story Dependency Map

```
US-001 (Upload)
  └─► US-008 (Batch upload)
  └─► US-013 (Error handling)
        └─► US-006 (Configure thresholds)
              └─► US-007 (Segment detail)
              └─► US-002 (Waveform view)
                    └─► US-009 (Agent transparency)
                    └─► US-003 (Dashboard)
                          └─► US-004 (Alerts)
                          └─► US-010 (Comparison)
                          └─► US-005 (Report download)
                                └─► US-012 (Regulatory export)
US-011 (Chatbot) — depends on US-007 + US-009
```

---

## Acceptance Criteria Summary

Each user story is considered complete when:

1. The described action can be performed end-to-end in the running application.
2. The benefit is demonstrable without additional steps.
3. Edge cases (empty files, invalid formats, threshold boundary values) are handled gracefully.
4. The feature passes QA review and relevant automated tests.
