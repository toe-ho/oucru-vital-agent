# 15. Risk Assessment

[← Back to Index](../00-index.md)

---

## Overview

This section identifies, quantifies, and provides mitigation strategies for risks that could impact the successful delivery of the Agentic AI for High-Frequency Data Quality Monitoring project.

**Risk Level Matrix:**

| Likelihood \ Impact | Low | Medium | High |
|---|---|---|---|
| **High** | Medium | High | Critical |
| **Medium** | Low | Medium | High |
| **Low** | Low | Low | Medium |

---

## Risk Register

| ID | Risk | Likelihood | Impact | Risk Level | Mitigation | Contingency |
|---|---|---|---|---|---|---|
| R-001 | **vital_sqi dependency conflicts** — vital_sqi supports Python >=3.7 (tested on 3.11) and runs directly in the backend container; risk is now dependency version conflicts between vital_sqi's pinned deps and other backend packages | Low | Low | Low | Pin all versions in `backend/requirements.txt`. Use `pip-compile` (pip-tools) for a conflict-free lock file. Run vital_sqi smoke tests in CI on every build. | If version conflicts arise, isolate conflicting packages using a virtual environment layer or pin the affected transitive dependency explicitly. |
| R-002 | **LLM reliability** — hallucination, inconsistent tool calling, wrong tool selection, producing invalid JSON outputs | High | High | Critical | Use smolagents with a restricted approved-tool registry, Ollama + Qwen3-8B, strict output validation with Pydantic schemas, and retry logic (max 3 attempts) with exponential backoff. | Fall back to rule-based classification using OUCRU signal tools if the agent fails to produce valid output after retries. Log all failures for post-hoc analysis. |
| R-003 | **Cloud budget exhaustion** — $2,000–$3,000 GCP credits (expires August 23, 2026) may be insufficient before project completion | Low | Medium | Low | Use local-first Ollama + Qwen3-8B for LLM work and reserve GCP spend for Cloud Run, Cloud SQL, and GCS. Track spend weekly with GCP budget alerts at 50%, 75%, 90% thresholds. | If GCP credits run low, keep the LLM runtime local and reduce always-on cloud resources during inactive development periods. |
| R-004 | **Agent latency** — LLM inference time adds 2–5 seconds per decision step; multi-step agent loops compound this for long recordings | High | Medium | High | Process segments in parallel where agent steps are independent. Cache LLM responses for identical or near-identical segment inputs. Batch multiple segment summaries into one LLM call where possible. Set per-segment timeouts. | Reduce agent reasoning depth (fewer ReAct steps) and accept slightly lower accuracy. Pre-compute SQI values synchronously; only invoke LLM for final classification and report generation. |
| R-005 | **Integration complexity** between TypeScript frontend and Python backend — CORS misconfiguration, type mismatches, API contract drift between teams | Medium | Medium | Medium | Define OpenAPI schema first; generate TypeScript client types from schema using `openapi-typescript`. Enforce schema validation on both sides. Use CORS middleware in FastAPI configured from environment variables. Write integration tests covering full request/response cycles. | If type generation tooling causes friction, manually maintain a shared `api-types.ts` file. Use Postman/Insomnia collections as contract reference. |
| R-006 | **Team learning curve** on smolagents, Docker, FastAPI, and Next.js — unfamiliarity may slow velocity in early sprints | High | Medium | High | Allocate Sprint 0 (2 weeks) exclusively for environment setup, tutorials, and prototype spikes. Pair experienced members with newer members on each stack layer. Maintain a team wiki with setup guides and code patterns. | Simplify the agent workflow to a deterministic sequential tool runner if smolagents proves too complex within schedule constraints. |
| R-007 | **vital_sqi edge cases** — corrupted files, unusual sampling rates, empty segments, unexpected channel names causing unhandled exceptions | Medium | Medium | Medium | Wrap all vital_sqi calls in try/except blocks. Validate file format and metadata before processing. Write unit tests for edge case inputs (empty signal, 0 Hz, NaN values). Define explicit error responses for each failure mode. | If a file cannot be processed, mark all its segments as `UNPROCESSABLE` and include in the report with error details. Never crash the pipeline; always return a partial result. |
| R-008 | **Scope overrun** — chatbot, deployment, and reporting polish increase execution risk if earlier phases slip | Medium | High | High | Maintain strict phase gates so Phase 5 begins with a fully stable Phase 4. Time-box chatbot and deployment hardening within Weeks 15–16. Prioritize reliable upload → assessment → report → chat demo flow over non-critical polish if time is constrained. | If core pipeline deliverables are not complete by Week 12, negotiate scope reduction with supervisor: live streaming and advanced analytics remain post-MVP scope. |
| R-013 | **Chatbot response quality** — LLM may produce vague or inaccurate explanations of segment rejection reasons; users may lose trust in the system | Medium | High | High | Ground chatbot responses exclusively in structured data from `agent_logs` and `sqi_results` tables; prohibit free-form hallucination. Write constrained system prompt with few-shot examples of good/bad explanations. Evaluate chatbot on 10 representative questions before delivery. | If response quality is insufficient, narrow chatbot scope to template-based answers using structured SQI data rather than free-form LLM generation. |
| R-009 | **Open-source LLM tool-calling quality** — incorrect function selection or malformed arguments from local Qwen3-8B | Medium | Medium | Medium | Restrict smolagents to approved tools, validate all arguments and outputs with Pydantic schemas, and keep deterministic rule-based classification for SQI/window decisions. | If tool-calling quality is insufficient, limit the LLM to final explanation/report text and run the analysis pipeline deterministically. |
| R-010 | **Data availability** — insufficient sample recordings from OUCRU for testing and validation; data access approval delays | Medium | High | High | Negotiate early access to a minimal anonymized dataset (5–10 recordings) in Sprint 1. Identify PhysioNet public datasets (MIT-BIH, MIMIC-III Waveform) as immediate substitutes. Generate synthetic noisy signals programmatically for unit tests. | Use entirely public datasets (PhysioNet) for all benchmarking if OUCRU data access is delayed beyond Sprint 2. Document this limitation in the final report. |
| R-011 | **Imaging scope ambiguity** — Original Objective 1 mentions "imaging and waveform" but project scopes to waveform only. Risk of client expectation mismatch. | Low | Medium | Low | Explicit scope-out documented in PRD goals/non-goals. Confirmed with OUCRU at kickoff. | Discuss imaging requirements and timeline at biweekly meeting. |
| R-012 | **vital_sqi maintenance** — If vital_sqi has bugs or missing features, team must fork and patch. | Low | Medium | Low | Pin to known-working `vitalSQI-toolkit==0.1.2`. Document any patches applied. Write smoke tests to catch regressions on upgrade. | Engage OUCRU maintainers for support; maintain a local fork only if upstream is unresponsive. |
| R-015 | **Ollama runtime dependency** — local LLM requires a running Ollama service and sufficient host resources for Qwen3-8B. | Medium | Medium | Medium | Include Ollama in Docker Compose, document model setup in `config.yaml`, and add a health check before starting agent jobs. Token-encoding layer still protects identifiers in prompts and logs. | If Ollama is unavailable, rule-based assessment mode produces quantitative results without LLM interpretation, and report narratives use deterministic templates. |
| R-016 | **Override governance drift** — human override behavior could become inconsistent across UI, API, reporting, and audit surfaces, causing trust and compliance issues. | Medium | High | High | Keep original AI classification immutable, use one append-only override-event model, enforce RBAC and required rationale fields, and test stale-report behavior explicitly. | Disable override write access temporarily and fall back to view-only adjudication until contract inconsistencies are fixed. |
| R-017 | **Unsafe feedback loop** — user overrides could be misinterpreted as direct online training signals, causing unreviewed production behavior changes. | Medium | High | High | Require staged collection, quality screening, offline evaluation, explicit admin approval, and rollback support before any promotion. | Freeze feedback export/promotion pipeline and continue collecting overrides for later manual review only. |

---

## Risk Priority Summary

| Priority | Risks |
|---|---|
| **Critical** | R-002 |
| **High** | R-004, R-006, R-008, R-010, R-013 |
| **Medium** | R-003, R-005, R-007, R-014, R-015 |
| **Low** | R-001, R-009, R-011, R-012 |

---

## Risk Review Schedule

- **Sprint Review (every 2 weeks):** Re-assess top-3 risks, update likelihood/impact based on new information.
- **Mid-project checkpoint (Week 6):** Full risk register review with supervisor.
- **Pre-delivery (Week 12):** Final risk review; document any unmitigated risks in project report.
