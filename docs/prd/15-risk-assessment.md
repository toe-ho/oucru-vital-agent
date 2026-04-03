# 15. Risk Assessment

[← Back to Index](00-index.md)

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
| R-002 | **LLM reliability** — hallucination, inconsistent tool calling, wrong tool selection, producing invalid JSON outputs | High | High | Critical | Dual-provider architecture with automatic fallback. Primary: Gemini 2.0 Flash via Vertex AI (production-grade tool-calling). If Gemini API is unavailable, system switches to Ollama self-hosted (Llama 3.1 8B). If both fail, agent falls back to rule-based processing using vital_sqi directly. Implement strict output validation with Pydantic schemas. Add retry logic (max 3 attempts) with exponential backoff. | Fall back to rule-based classification pipeline (vital_sqi standalone) if agent fails to produce valid output after retries. Log all failures for post-hoc analysis. |
| R-003 | **Cloud budget exhaustion** — $2,000–$3,000 GCP credits (expires August 23, 2026) may be insufficient before project completion | Low | Medium | Low | Gemini API costs are covered by existing GCP credits. Estimated API cost: <$20/month for project volume. No dedicated GPU VM required — switching from self-hosted T4 GPU to Gemini API reduces monthly cloud cost by ~60%. Track spend weekly with GCP budget alerts at 50%, 75%, 90% thresholds. | If GCP credits run low, switch `LLM_PROVIDER=ollama` to activate the self-hosted Ollama fallback at zero API cost. |
| R-004 | **Agent latency** — LLM inference time adds 2–5 seconds per decision step; multi-step agent loops compound this for long recordings | High | Medium | High | Process segments in parallel where agent steps are independent. Cache LLM responses for identical or near-identical segment inputs. Batch multiple segment summaries into one LLM call where possible. Set per-segment timeouts. | Reduce agent reasoning depth (fewer ReAct steps) and accept slightly lower accuracy. Pre-compute SQI values synchronously; only invoke LLM for final classification and report generation. |
| R-005 | **Integration complexity** between TypeScript frontend and Python backend — CORS misconfiguration, type mismatches, API contract drift between teams | Medium | Medium | Medium | Define OpenAPI schema first; generate TypeScript client types from schema using `openapi-typescript`. Enforce schema validation on both sides. Use CORS middleware in FastAPI configured from environment variables. Write integration tests covering full request/response cycles. | If type generation tooling causes friction, manually maintain a shared `api-types.ts` file. Use Postman/Insomnia collections as contract reference. |
| R-006 | **Team learning curve** on LangGraph, Docker, FastAPI — unfamiliarity may slow velocity in early sprints | High | Medium | High | Allocate Sprint 0 (2 weeks) exclusively for environment setup, tutorials, and prototype spikes. Pair experienced members with newer members on each stack layer. Maintain a team wiki with setup guides and code patterns. | Simplify agent framework: replace LangGraph state machine with a simpler sequential chain (LangChain LCEL) if LangGraph proves too complex to learn within schedule constraints. |
| R-007 | **vital_sqi edge cases** — corrupted files, unusual sampling rates, empty segments, unexpected channel names causing unhandled exceptions | Medium | Medium | Medium | Wrap all vital_sqi calls in try/except blocks. Validate file format and metadata before processing. Write unit tests for edge case inputs (empty signal, 0 Hz, NaN values). Define explicit error responses for each failure mode. | If a file cannot be processed, mark all its segments as `UNPROCESSABLE` and include in the report with error details. Never crash the pipeline; always return a partial result. |
| R-008 | **Scope overrun** — chatbot interface, token-encoding privacy layer, and real-time streaming are now core deliverables; this increases execution risk if earlier phases slip | Medium | High | High | Maintain strict phase gates so Phase 5 begins with a fully stable Phase 4. Time-box chatbot and token-encoding implementation within Weeks 15–16. Prioritize chatbot and token-encoding over GCP deployment polish if time is constrained. | If core pipeline deliverables are not complete by Week 12, negotiate scope reduction with supervisor: real-time streaming may be deferred, but chatbot and token-encoding remain in scope. |
| R-013 | **Chatbot response quality** — LLM may produce vague or inaccurate explanations of segment rejection reasons; users may lose trust in the system | Medium | High | High | Ground chatbot responses exclusively in structured data from `agent_logs` and `sqi_results` tables; prohibit free-form hallucination. Write constrained system prompt with few-shot examples of good/bad explanations. Evaluate chatbot on 10 representative questions before delivery. | If response quality is insufficient, narrow chatbot scope to template-based answers using structured SQI data rather than free-form LLM generation. |
| R-014 | **Token-encoding implementation complexity** — reversible pseudonymization with a stored mapping table requires careful key management and introduces new failure modes (data unrecoverable if mapping lost) | Low | High | Medium | Use a simple deterministic UUID-based mapping stored in a dedicated `patient_id_mappings` DB table. Back up mapping table separately. Implement and test round-trip encode/decode before connecting to the LLM pipeline. | If mapping-based approach proves too complex, fall back to a hash-based pseudonymization (one-way) with a clear warning that re-identification is not possible without original data. |
| R-009 | **Open-source LLM tool-calling quality** inferior to proprietary models — incorrect function selection, malformed arguments | Low | Low | Low | Mitigated by using Gemini 2.0 Flash as primary provider, which has production-grade tool-calling with native function calling support. Ollama/Llama 3.1 8B is only used as optional fallback. If Ollama tool-calling quality is insufficient during local testing, keep Gemini as the primary and limit Ollama to offline/demo scenarios only. | Not applicable for Gemini primary path. For Ollama fallback: restrict to read-only tools (query_history, get_segment_detail) and use rule-based classification for segment decisions. |
| R-010 | **Data availability** — insufficient sample recordings from OUCRU for testing and validation; data access approval delays | Medium | High | High | Negotiate early access to a minimal anonymized dataset (5–10 recordings) in Sprint 1. Identify PhysioNet public datasets (MIT-BIH, MIMIC-III Waveform) as immediate substitutes. Generate synthetic noisy signals programmatically for unit tests. | Use entirely public datasets (PhysioNet) for all benchmarking if OUCRU data access is delayed beyond Sprint 2. Document this limitation in the final report. |
| R-011 | **Imaging scope ambiguity** — Original Objective 1 mentions "imaging and waveform" but project scopes to waveform only. Risk of client expectation mismatch. | Low | Medium | Low | Explicit scope-out documented in PRD goals/non-goals. Confirmed with OUCRU at kickoff. | Discuss imaging requirements and timeline at biweekly meeting. |
| R-012 | **vital_sqi maintenance** — If vital_sqi has bugs or missing features, team must fork and patch. | Low | Medium | Low | Pin to known-working `vitalSQI-toolkit==0.1.2`. Document any patches applied. Write smoke tests to catch regressions on upgrade. | Engage OUCRU maintainers for support; maintain a local fork only if upstream is unresponsive. |
| R-015 | **Gemini API dependency** — primary LLM requires internet access and active GCP credentials. Outages or credential expiry would block all assessments. | Low | High | Medium | Ollama fallback activated automatically when Gemini is unreachable (`LLM_PROVIDER=ollama`). Token-encoding layer ensures no sensitive data is sent to the API regardless of provider. Monitor Vertex AI status page. Rotate service account credentials before expiry. | If Gemini is unavailable for an extended period, switch to `LLM_PROVIDER=ollama` for continuity. If both providers fail, rule-based assessment mode (vital_sqi standalone) produces quantitative results without LLM interpretation. |

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
