# 01 — Executive Summary

[← Back to Index](00-index.md)

---

## Project Identity

| Field       | Value |
|-------------|-------|
| Project     | Agentic AI for High-Frequency Data Quality Monitoring |
| Client      | OUCRU — Oxford University Clinical Research Unit |
| Domain      | Clinical Research / Medical Signal Processing |
| Version     | 1.0 |
| Date        | 2026-04-03 |

---

## Problem

OUCRU continuously collects high-frequency physiological waveform data (ECG, PPG) from wearable devices and bedside monitors across multiple clinical research studies. The data pipeline ingests recordings that may span hours per subject per session, and data quality issues — sensor disconnection, patient movement artifacts, electrical interference — are common.

Current quality control relies on two mechanisms: static rule-based checks applied at ingestion time, and periodic manual review by clinical researchers and data engineers. Neither scales:

- **Static rules** cannot reason about context, handle source-specific noise profiles, or adapt to new devices without manual reconfiguration.
- **Manual review** is slow, expensive, inconsistent across reviewers, and cannot keep pace with growing data volume.

The result is delayed detection of quality issues, compromised research data integrity, wasted clinical resources, and potential regulatory risk.

---

## Solution

Build an **agentic AI system** that autonomously monitors waveform data quality end-to-end — from file upload through signal assessment to report generation — without manual intervention.

The system uses an LLM-powered agent (Google Gemini 2.0 Flash via Vertex AI as primary, with open-source fallback via Ollama) as the orchestration "brain." The LLM does not perform signal processing; it reasons about which quality assessment tools to invoke, interprets their outputs, and synthesizes findings into actionable reports. OUCRU's existing `vital_sqi` Python library serves as the "toolbox" — the agent calls `vital_sqi` functions via a structured tool-wrapper layer.

> **Critical design constraint:** The team does NOT build new signal processing algorithms or ML models for quality detection. All signal assessment logic resides in `vital_sqi`. The agent's value is in orchestration, contextual reasoning, and communication.

> **Scope Note:** While OUCRU's Objective 1 references both imaging and waveform data, imaging data quality is explicitly deferred to future phases. This project focuses exclusively on waveform data (ECG, PPG).

---

## Key Deliverables

| Component | Description |
|-----------|-------------|
| **Tool Wrappers** | Python wrappers exposing `vital_sqi` functions as structured agent tools |
| **Agent Orchestration Layer** | LLM-based agent (Gemini via Vertex AI primary; Ollama open-source fallback) that plans and executes quality checks |
| **REST API Backend** | FastAPI service exposing upload, assessment, and report endpoints |
| **Web Dashboard** | React/TypeScript dashboard for medical practitioners to upload data and view results |
| **Automated Report Generation** | Structured PDF/JSON quality reports generated without manual intervention |
| **Chatbot Interface** | Natural language query interface allowing practitioners to ask questions about quality results |
| **Token-Encoding Privacy Layer** | Anonymisation/encoding layer for waveform metadata before transmission to any external LLM API |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Reporting time reduction | ≥ 50% reduction vs. current manual baseline |
| Defect detection improvement | ≥ 20% improvement in precision and recall vs. static rule baseline |
| Report generation | Fully automated — zero manual steps required post-upload |
| Dashboard availability | 99% uptime during working hours *(team-proposed target — not a client-specified requirement)* |

---

## Budget & Infrastructure

| Item | Detail |
|------|--------|
| Cloud platform | Google Cloud Platform (GCP) |
| Budget | ~$2,000–$3,000 GCP credits |
| LLM | Google Gemini 2.0 Flash via Vertex AI (primary, covered by GCP credits); Ollama + Llama 3.1 8B (optional self-hosted fallback) |
| Signal processing | `vital_sqi` open-source library — no licensing cost |
