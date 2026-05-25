# 06 — Functional Requirements

[← Back to Index](../00-index.md)

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

---

## a. Data Ingestion Module

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-001 | The system shall accept ECG file uploads in EDF (.edf), MIT/WFDB (.hea + .dat), CSV (.csv), and Parquet (.parquet) formats. | Must | Data Ingestion |
| FR-002 | The system shall accept PPG file uploads in CSV (.csv) and Parquet (.parquet) formats with configurable column mapping for signal, timestamp, and sampling rate. | Must | Data Ingestion |
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
| FR-011 | The system shall integrate OUCRU signal-processing tools through registered agent functions. For ECG-oriented quality checks, the agent shall load the waveform with `load_signal_file()`, compute quality with `compute_sqi()` or `compute_sqi_windowed()`, and derive clinical/quality flags with downstream threshold checks. | Must | SQA |
| FR-012 | The system shall integrate OUCRU signal-processing tools through registered agent functions. For PPG quality assessment, the agent shall use `load_signal_file()`, optionally `preprocess_ppg()`, compute quality with `compute_sqi()` or `compute_sqi_windowed()`, and derive clinical/quality flags with `check_clinical_thresholds()`. | Must | SQA |
| FR-013 | The system shall segment signals into fixed-duration windows with configurable segment duration (default: 30 seconds), configurable overlap (default: 0%), and configurable split type (fixed-time vs. beat-based). | Must | SQA |
| FR-014 | The system shall support selection of SQI metrics from a catalog of 47+ metrics spanning eight categories: Statistical (e.g., kurtosis, skewness, entropy), Signal Processing (e.g., SNR, zero-crossing rate), Cardiac-Specific (e.g., QRS energy, ectopic beat fraction), Frequency/Energy (e.g., band energy), HRV Time Domain (e.g., SDNN, RMSSD), Heart Rate (e.g., HR mean, HR range), Power Spectral (e.g., LF/HF ratio, absolute power), and Nonlinear (e.g., Poincaré SD1/SD2, DTW distance). | Must | SQA |
| FR-015 | The system shall allow per-metric threshold configuration via a `rule_dict` structure (JSON), specifying accept/reject boundaries for each selected SQI metric. | Must | SQA |
| FR-016 | The system shall produce a per-segment classification output (accept / reject) based on the configured thresholds, storing the decision alongside all computed SQI values. | Must | SQA |
| FR-017 | The system shall support multi-channel ECG quality assessment, computing SQIs independently per channel and aggregating to a single segment decision using a configurable aggregation strategy (e.g., all-pass, majority-vote). | Must | SQA |
| FR-018 | The system shall handle vital_sqi processing errors (e.g., insufficient beats detected, flat-line signal) gracefully, marking affected segments as "uncomputable" rather than crashing the pipeline. | Must | SQA |
| FR-019 | The system shall expose a preprocessing step (bandpass filter, baseline wander removal) configurable per signal type, applied before SQI computation. | Should | SQA |
| FR-020 | The system shall store all computed SQI values, segment timestamps, and classification decisions in persistent storage linked to the recording ID for later retrieval. | Must | SQA |
| FR-020A | The system shall preserve the original AI-generated segment `classification` as an immutable generated output. Human review shall not overwrite `segments.classification`. | Must | SQA |
| FR-020B | The system shall derive an `effective_classification` for UI and report use: active override label if one exists, otherwise the original AI `classification`. | Must | SQA |

---

## c. Agentic AI Orchestration Module (Core Module)

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-021 | The system shall implement an AI agent that orchestrates the full quality monitoring pipeline using a tool-calling interface. | Must | Agent |
| FR-022 | The agent shall expose the following OUCRU analysis tools: `load_signal_file`, `preprocess_ppg`, `compute_sqi`, `compute_sqi_windowed`, `extract_hrv_features`, `estimate_spo2`, `extract_ppg_dc_layer`, and `check_clinical_thresholds`. Each tool shall have a documented input schema and output schema. | Must | Agent |
| FR-023 | The `load_signal_file` tool shall accept a signal file path plus optional column and sampling-rate parameters, load CSV or Parquet waveform data, and return signal samples with sampling metadata. | Must | Agent |
| FR-024 | The `compute_sqi` tool shall accept a signal array, sampling rate, and signal type, then return an overall signal quality score suitable for ECG or PPG quality screening. | Must | Agent |
| FR-025 | The `compute_sqi_windowed` tool shall accept a signal array, sampling rate, signal type, and window configuration, then return per-window SQI values for segment-level quality analysis. | Must | Agent |
| FR-026 | The `preprocess_ppg` tool shall filter, normalize, and detect peaks in PPG signals before downstream PPG-specific analysis. | Should | Agent |
| FR-027 | The `extract_hrv_features` tool shall accept RR intervals and return time-domain and frequency-domain HRV features for clinical interpretation. | Should | Agent |
| FR-028 | The `estimate_spo2` tool shall estimate oxygen saturation from red and infrared PPG channels when those channels are available. | Should | Agent |
| FR-029 | The `extract_ppg_dc_layer` tool shall extract the DC component from a PPG signal for perfusion and trend analysis. | Should | Agent |
| FR-030 | The `check_clinical_thresholds` tool shall accept heart rate, SpO2, and SQI values and return structured clinical/quality flags for agent interpretation and escalation. | Must | Agent |
| FR-031 | The agent shall implement an observe → think → act → interpret → repeat decision loop, with each iteration logged with a timestamp, action type, inputs, outputs, and reasoning text. | Must | Agent |
| FR-032 | The agent shall maintain context across pipeline steps within a single session: uploaded file metadata, preprocessing configuration, intermediate SQI results, and partial classifications shall persist in the agent's working memory for the duration of the job. | Must | Agent |
| FR-033 | The agent shall handle the following error conditions without terminating the pipeline: corrupted input file (skip file, log error), vital_sqi computation failure on a segment (mark as uncomputable, continue), LLM API failure (retry up to 3 times with exponential backoff, then fall back to rule-based decision). | Must | Agent |
| FR-034 | The agent shall log every decision, tool invocation, parameter used, and reasoning step to a persistent agent log associated with the recording ID. This log shall be readable by end users via the dashboard. | Must | Agent |
| FR-035 | The agent shall apply escalation rules: if overall quality score falls below a configurable critical threshold (default: 40% accepted segments), the agent shall emit an alert event and flag the recording for human review rather than auto-accepting the result. | Must | Agent |

---

## d. Automated Reporting Module

| ID | Requirement | Priority | Module |
|---|---|---|---|
| FR-036 | The system shall generate a canonical JSON quality report payload for each processed recording containing: recording metadata, overall quality score, accept/reject segment counts, per-segment SQI summary table, timeline of quality across the recording, flagged issues list, automated recommendations, confidence, skipped steps, and limitations. | Must | Reporting |
| FR-037 | The system shall support report export in PDF format rendered from the canonical JSON payload, with a professional layout suitable for inclusion in clinical study documentation. | Must | Reporting |
| FR-038 | The system shall support report export in HTML format rendered from the canonical JSON payload for browser-based viewing without additional software. | Should | Reporting |
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
| FR-050 | The Quality Dashboard shall update automatically by polling job status when a background processing job completes, without requiring a page refresh. Live waveform streaming is post-MVP scope. | Should | Dashboard |
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
