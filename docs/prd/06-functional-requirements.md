# 06 — Functional Requirements

[← Back to Index](00-index.md)

---

## Overview

This document specifies all functional requirements for the **Agentic AI for High-Frequency Data Quality Monitoring** system. Requirements are organized by module and assigned unique identifiers for traceability. Priority levels follow MoSCoW: **Must** (mandatory), **Should** (high value), **Could** (nice to have).

> **Note:** Specific numeric thresholds (file size limits, batch sizes, metric counts, timing targets) are proposed defaults based on team analysis. These require validation with OUCRU during development.

---

## Module Index

| Module | ID Range | Description |
|---|---|---|
| Data Ingestion | FR-001 – FR-010 | File upload, validation, storage, metadata extraction |
| Signal Quality Assessment | FR-011 – FR-020 | vital_sqi integration, segmentation, SQI computation, classification |
| Agentic AI Orchestration | FR-021 – FR-035 | Agent tools, decision loop, transparency, escalation |
| Automated Reporting | FR-036 – FR-045 | Report generation, formats, triggers, export |
| Web Dashboard | FR-046 – FR-060 | Monitoring screen, quality dashboard, upload UI, settings |
| Chatbot Interface | FR-061 – FR-065 | Natural language queries, threshold configuration via chat |
| Token-Encoding Privacy Layer | FR-066 – FR-068 | Identifier metadata encoding before LLM transmission |

---

## a. Data Ingestion Module

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-001 | The system shall accept ECG file uploads in EDF (.edf), MIT/WFDB (.hea + .dat), and CSV (.csv) formats. | Must | Data Ingestion |
| FR-002 | The system shall accept PPG file uploads in CSV (.csv) format with configurable column mapping for signal, timestamp, and sampling rate. | Must | Data Ingestion |
| FR-003 | The system shall validate uploaded files for format correctness, presence of required headers/channels, minimum sampling rate (≥ 100 Hz for ECG, ≥ 25 Hz for PPG), and minimum recording duration (≥ 10 seconds). | Must | Data Ingestion |
| FR-004 | The system shall detect and reject corrupted files (truncated data, invalid EDF headers, non-numeric signal values) and return a structured error response with a human-readable message specifying the failure reason. | Must | Data Ingestion |
| FR-005 | The system shall extract and store file metadata on upload: original filename, file size, signal type (ECG/PPG), sampling rate, recording duration, number of channels, and upload timestamp. | Must | Data Ingestion |
| FR-006 | The system shall support multi-channel ECG files and allow the user to select which channel(s) to process during upload or configuration. | Must | Data Ingestion |
| FR-007 | The system shall enforce a maximum individual file size of 500 MB and return an appropriate error if this limit is exceeded. | Must | Data Ingestion |
| FR-008 | The system shall support batch upload of up to 50 files in a single request, processing each file as an independent pipeline job. | Should | Data Ingestion |
| FR-009 | The system shall persist uploaded files to backend storage (local filesystem or object storage) and associate each file with a unique recording ID. | Must | Data Ingestion |
| FR-010 | The system shall display real-time upload progress (percentage and estimated time remaining) for files larger than 10 MB. | Should | Data Ingestion |

---

## b. Signal Quality Assessment Module

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-011 | The system shall integrate with the `vital_sqi` library and invoke `get_ecg_sqis()` and `get_qualified_ecg()` for ECG quality assessment. | Must | SQA |
| FR-012 | The system shall integrate with the `vital_sqi` library and invoke `get_ppg_sqis()` and `get_qualified_ppg()` for PPG quality assessment. | Must | SQA |
| FR-013 | The system shall segment signals into fixed-duration windows with configurable segment duration (default: 30 seconds), configurable overlap (default: 0%), and configurable split type (fixed-time vs. beat-based). | Must | SQA |
| FR-014 | The system shall support selection of SQI metrics from a catalog of 47+ metrics spanning eight categories: Statistical (e.g., kurtosis, skewness, entropy), Signal Processing (e.g., SNR, zero-crossing rate), Cardiac-Specific (e.g., QRS energy, ectopic beat fraction), Frequency/Energy (e.g., band energy), HRV Time Domain (e.g., SDNN, RMSSD), Heart Rate (e.g., HR mean, HR range), Power Spectral (e.g., LF/HF ratio, absolute power), and Nonlinear (e.g., Poincaré SD1/SD2, DTW distance). | Must | SQA |
| FR-015 | The system shall allow per-metric threshold configuration via a `rule_dict` structure (JSON), specifying accept/reject boundaries for each selected SQI metric. | Must | SQA |
| FR-016 | The system shall produce a per-segment classification output (accept / reject) based on the configured thresholds, storing the decision alongside all computed SQI values. | Must | SQA |
| FR-017 | The system shall support multi-channel ECG quality assessment, computing SQIs independently per channel and aggregating to a single segment decision using a configurable aggregation strategy (e.g., all-pass, majority-vote). | Must | SQA |
| FR-018 | The system shall handle vital_sqi processing errors (e.g., insufficient beats detected, flat-line signal) gracefully, marking affected segments as "uncomputable" rather than crashing the pipeline. | Must | SQA |
| FR-019 | The system shall expose a preprocessing step (bandpass filter, baseline wander removal) configurable per signal type, applied before SQI computation. | Should | SQA |
| FR-020 | The system shall store all computed SQI values, segment timestamps, and classification decisions in persistent storage linked to the recording ID for later retrieval. | Must | SQA |

---

## c. Agentic AI Orchestration Module (Core Module)

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-021 | The system shall implement an AI agent that orchestrates the full quality monitoring pipeline using a tool-calling interface. | Must | Agent |
| FR-022 | The agent shall expose the following tools: `assess_ecg_quality`, `assess_ppg_quality`, `compute_ecg_sqis`, `compute_ppg_sqis`, `preprocess_signal`, `generate_report`, `query_history`, `get_segment_detail`. Each tool shall have a documented input schema and output schema. | Must | Agent |
| FR-023 | The `assess_ecg_quality` tool shall accept a recording ID, invoke preprocessing and SQI computation, classify segments, and return a structured summary (total segments, accepted count, rejected count, overall quality score). | Must | Agent |
| FR-024 | The `assess_ppg_quality` tool shall perform the equivalent workflow for PPG signals, returning the same structured summary format as `assess_ecg_quality`. | Must | Agent |
| FR-025 | The `compute_ecg_sqis` tool shall accept a recording ID and segment index and return all computed SQI values for that segment. | Must | Agent |
| FR-026 | The `compute_ppg_sqis` tool shall perform the equivalent SQI computation for a PPG segment. | Must | Agent |
| FR-027 | The `preprocess_signal` tool shall apply configurable preprocessing (filter type, cutoff frequencies, baseline correction) to a raw signal segment and return the processed signal. | Should | Agent |
| FR-028 | The `generate_report` tool shall compile assessment results into a structured report object and persist it, returning the report ID and download URL. | Must | Agent |
| FR-029 | The `query_history` tool shall accept a recording ID or study ID and return historical assessment results, enabling trend queries. | Should | Agent |
| FR-030 | The `get_segment_detail` tool shall return the full detail for a given segment: raw SQI values, threshold comparisons, classification decision, and a natural-language explanation of why the segment was accepted or rejected. | Must | Agent |
| FR-031 | The agent shall implement an observe → think → act → interpret → repeat decision loop, with each iteration logged with a timestamp, action type, inputs, outputs, and reasoning text. | Must | Agent |
| FR-032 | The agent shall maintain context across pipeline steps within a single session: uploaded file metadata, preprocessing configuration, intermediate SQI results, and partial classifications shall persist in the agent's working memory for the duration of the job. | Must | Agent |
| FR-033 | The agent shall handle the following error conditions without terminating the pipeline: corrupted input file (skip file, log error), vital_sqi computation failure on a segment (mark as uncomputable, continue), LLM API failure (retry up to 3 times with exponential backoff, then fall back to rule-based decision). | Must | Agent |
| FR-034 | The agent shall log every decision, tool invocation, parameter used, and reasoning step to a persistent agent log associated with the recording ID. This log shall be readable by end users via the dashboard. | Must | Agent |
| FR-035 | The agent shall apply escalation rules: if overall quality score falls below a configurable critical threshold (default: 40% accepted segments), the agent shall emit an alert event and flag the recording for human review rather than auto-accepting the result. | Must | Agent |

---

## d. Automated Reporting Module

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-036 | The system shall generate a quality report for each processed recording containing: recording metadata, overall quality score, accept/reject segment counts, per-segment SQI summary table, timeline of quality across the recording, flagged issues list, and automated recommendations. | Must | Reporting |
| FR-037 | The system shall support report export in PDF format, with a professional layout suitable for inclusion in clinical study documentation. | Must | Reporting |
| FR-038 | The system shall support report export in HTML format for browser-based viewing without additional software. | Should | Reporting |
| FR-039 | The system shall provide an in-app report viewer that renders the report content within the web dashboard without requiring download. | Should | Reporting |
| FR-040 | The system shall support on-demand report generation triggered by the user via the dashboard for any previously processed recording. | Must | Reporting |
| FR-041 | The system shall automatically generate a report upon completion of each recording's processing pipeline. | Should | Reporting |
| FR-042 | The system shall support scheduled report generation (e.g., daily summary of all recordings processed that day) configurable by the Data Engineer. | Could | Reporting |
| FR-043 | Reports shall include a historical comparison section when two or more recordings from the same patient or study are available, showing quality trend over time. | Should | Reporting |
| FR-044 | All generated reports shall be stored persistently and accessible via a unique report URL for at least 90 days. | Must | Reporting |
| FR-045 | The system shall support bulk export of multiple reports as a ZIP archive. | Could | Reporting |

---

## e. Web Dashboard

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-046 | The system shall provide a **Monitoring Screen** that displays the raw waveform of a selected recording with a quality overlay rendered as colored segments (green = accepted, red = rejected, yellow = uncomputable) on the same time axis. | Must | Dashboard |
| FR-047 | The Monitoring Screen shall allow the user to navigate between segments using previous/next controls and by clicking directly on the waveform timeline. | Must | Dashboard |
| FR-048 | The Monitoring Screen shall display the current segment's SQI scores in a sidebar panel, showing metric name, computed value, threshold, and pass/fail status for each active metric. | Must | Dashboard |
| FR-049 | The system shall provide a **Quality Dashboard** screen showing: overall quality score (percentage), accept/reject ratio as a horizontal bar, a timeline heatmap of quality across all segments, an active alerts list, and trend charts comparing quality across multiple recordings. | Must | Dashboard |
| FR-050 | The Quality Dashboard shall update automatically (polling or WebSocket) when a background processing job completes, without requiring a page refresh. | Should | Dashboard |
| FR-051 | The system shall provide a **File Upload** interface with drag-and-drop support, file type validation on the client side, and a progress indicator per file. | Must | Dashboard |
| FR-052 | The File Upload interface shall display the list of queued, in-progress, and completed uploads with status indicators and error messages for failed uploads. | Must | Dashboard |
| FR-053 | The system shall provide a **Report Viewer** screen that renders the in-app report and provides download buttons for PDF and HTML formats. | Must | Dashboard |
| FR-054 | The system shall provide a **Settings / Configuration** page where authorized users can modify SQI thresholds (rule_dict), segment duration, overlap, metric selection, and alert thresholds, with changes persisted to backend storage. | Must | Dashboard |
| FR-055 | The Settings page shall validate threshold inputs and display inline validation errors before saving. | Must | Dashboard |
| FR-056 | The system shall provide a **Recording List** screen showing all uploaded recordings with columns: filename, upload date, signal type, duration, overall quality score, processing status, and quick-action buttons (view, report, delete). | Must | Dashboard |
| FR-057 | The Recording List shall support sorting by any column and filtering by signal type, date range, and quality score range. | Should | Dashboard |
| FR-058 | The system shall provide a **Segment Detail** modal/panel accessible from the waveform view, showing: segment waveform excerpt, all SQI metric values, threshold comparison table, agent decision, and natural-language explanation from the agent log. | Must | Dashboard |
| FR-059 | The system shall provide an **Agent Log Viewer** accessible per recording, displaying the agent's full decision log in a readable timeline format (timestamp, action, tool called, reasoning). | Must | Dashboard |
| FR-060 | The dashboard shall be fully functional on desktop (1280px+) and tablet (768px–1279px) screen sizes using responsive layout. | Must | Dashboard |

---

## f. Chatbot Interface

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-061 | The system shall provide a chatbot interface that accepts natural language queries about quality assessment results for a selected recording or study. | Must | Chatbot |
| FR-062 | The chatbot shall be able to answer queries such as "Why was segment 45 rejected?", "What is the average kurtosis for today's recordings?", and "How many recordings passed the quality threshold this week?" by invoking the appropriate agent tools. | Must | Chatbot |
| FR-063 | The chatbot shall explain the rejection reason for any segment in plain English, translating SQI metric names and threshold values into clinically meaningful language (e.g., "The signal was too noisy — the kurtosis value of 2.1 was below the minimum threshold of 5.0"). | Must | Chatbot |
| FR-064 | The chatbot shall assist users in configuring SQI thresholds by answering questions like "What threshold should I use for SSQI?" and referencing literature-recommended values. | Should | Chatbot |
| FR-065 | The chatbot shall explain medical and signal processing terminology on request (e.g., "What is SDNN?", "What does HRV frequency domain mean?"). | Should | Chatbot |

---

## g. Token-Encoding Privacy Layer

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-066 | The system shall implement a configurable privacy encoding layer that encodes patient-identifiable metadata (subject IDs, device IDs, timestamps, filenames) in all prompts sent to external LLM providers. Raw waveform signal data (numeric arrays) is not sent to the LLM and does not require encoding. | Must | Privacy Layer |
| FR-067 | The system shall implement a corresponding decoding step that reverses the identifier substitution in LLM responses, restoring original values before they are written to agent logs or returned to the API layer. | Must | Privacy Layer |
| FR-068 | The identifier encoding strategy (deterministic placeholder substitution with a session-scoped mapping table) shall be configurable per deployment and documented with its privacy guarantees. | Should | Privacy Layer |
