# 17. Acceptance Criteria

[← Back to Index](../00-index.md)

---

## Overview

Acceptance criteria define the measurable conditions that must be satisfied for each deliverable to be considered complete. These criteria form the contractual definition of done between the development team and the project supervisor/client (OUCRU).

---

## Acceptance Criteria Table

| ID | Deliverable | Criterion | Measurement Method | Target |
|---|---|---|---|---|
| AC-001 | End-to-End Pipeline | Pipeline processes a 1-hour recording without manual intervention from file upload to final report | Upload recording, monitor pipeline logs, verify report is generated without human input | Zero manual steps required after initial upload |
| AC-002 | Processing Time | Total pipeline time for a 1-hour ECG or PPG recording from upload to completed report | Automated timing test: `pytest tests/performance/test_pipeline_throughput.py` | < 10 minutes wall time |
| AC-003 | Dashboard Load | Dashboard displays session results within 3 seconds of page load on a standard broadband connection | Lighthouse CI measurement of First Contentful Paint and Time to Interactive | FCP < 3 seconds, TTI < 3 seconds |
| AC-004 | Report Generation | Automatically generated reports contain all four required sections | Parse generated report JSON/HTML and assert presence of all sections | 100% of reports contain: (1) executive summary, (2) segment timeline, (3) flagged issues list, (4) recommendations |
| AC-005 | Agent Transparency | Agent decision log records every tool call, input arguments, output, and reasoning chain for every recording assessment | Inspect agent log output; assert tool call count and reasoning fields are non-empty | 100% of tool invocations logged with reasoning; zero silent failures |
| AC-006 | Time Reduction | Automated pipeline reduces reporting time by ≥ 50% compared to manual human review baseline | Benchmark study: 5 recordings timed manually by domain expert vs. automated pipeline; calculate reduction % | Mean reduction ≥ 50% across 5 benchmark recordings |
| AC-007 | Detection Improvement | Agent-assisted classification achieves ≥ 20% improvement in defect detection rate vs. vital_sqi rule-based-only classification, measured as improvement in both precision and recall (or F1 as composite) | Evaluate both classifiers on labeled test set (≥ 200 segments); compute precision/recall/F1 | ≥ 20% improvement in both precision and recall, or ≥ 20% F1 improvement as composite |
| AC-008 | Code Quality | All code is documented, follows project code standards, and is publicly available on GitHub | Code review checklist; verify public GitHub repository URL is accessible | Public GitHub repository with README, docstrings on all public functions, no hardcoded secrets |
| AC-009 | Deployment | Entire application stack starts from a single command using Docker Compose | `docker compose up` on a clean machine; verify frontend, backend, and database are all accessible | All services start healthy within 5 minutes; no manual configuration required beyond `.env` file |
| AC-010 | File Format Support | System correctly loads, processes, and reports results for all supported input formats | Submit one file in each format; verify results are returned without errors | EDF: pass, MIT/WFDB: pass, CSV (ECG): pass, CSV (PPG): pass |
| AC-011 | Multi-Channel Support | System handles multi-channel ECG recordings when provided. Single-channel support is the baseline requirement; multi-channel is a should-have. | Submit a 12-lead EDF recording; verify report contains metrics for each channel | Single-channel: must pass. Multi-channel (12-lead): should pass; not a hard requirement for MVP acceptance |
| AC-012 | Classification Accuracy | Agent classification aligns with vital_sqi standalone classification for clearly-good and clearly-bad segments. Divergence is expected and encouraged for edge cases where the agent's contextual reasoning improves detection (see AC-007). | Run both classifiers on the same 200-segment test set; compute agreement rate on clearly-good and clearly-bad segments separately from ambiguous/borderline segments | Agreement rate on clearly-good and clearly-bad segments ≥ 95%; improvement target (AC-007) is measured on ambiguous/borderline segments |
| AC-013 | Error Handling | System handles corrupted or malformed input files gracefully without crashing | Submit 5 corrupted files (truncated header, zero-length signal, wrong extension, binary garbage, partial write) | All 5 files return structured error response with `status: ERROR` and human-readable message; no 500 server crashes |
| AC-014 | Dashboard Completeness | Both primary dashboard views are functional and display accurate data | Manual walkthrough of Monitoring Screen and Quality Dashboard; verify all data fields populated | Monitoring Screen: session list, status, timestamps functional. Quality Dashboard: segment timeline, SQI charts, agent log functional |
| AC-015 | Report Export | Reports are exportable in both PDF and HTML formats with complete content | Click export buttons for both formats; verify downloaded files open correctly and contain all report sections | PDF export: renders with all sections. HTML export: self-contained file opens in browser without external dependencies |
| AC-017 | Chatbot Interface | Chatbot answers questions about segment rejection with accurate SQI-grounded explanations; responses reference actual metric values from the queried recording | Submit 5 representative questions about a completed recording's rejected segments; verify each response contains at least one specific SQI metric name and value matching the stored `sqi_results` data | ≥ 4 of 5 test questions receive a response that references correct, recording-specific SQI data; zero responses contain fabricated metric values |
| AC-018 | Segment Override Governance | Only `admin` and `reviewer` can create a segment override, using label `accept` or `reject` plus required reason category and note, without overwriting the original AI classification | Exercise override API/UI with each role and invalid payload variants | Authorized roles succeed; unauthorized roles receive `403`; invalid label or missing rationale receives `400`; original `segments.classification` remains unchanged |
| AC-019 | Override History | Changing an existing override creates a new superseding override event rather than deleting or mutating prior override history | Create one override, then change it once, and inspect stored history plus read model | History shows two append-only events, exactly one active override, and correct `effective_classification` |
| AC-020 | Stale Report Warning | A report generated before a later segment override is clearly marked stale and is not silently regenerated | Generate report, apply later override, then open existing report and report list | Existing report remains accessible, displays stale warning, and no automatic regeneration occurs |
| AC-021 | Safe Active Learning | Feedback-derived learning follows collection → quality screen/export → offline evaluation → admin approval → promotion/rollback gates with no immediate production mutation from a single override | Review pipeline records and approval checkpoints in staging workflow | No direct production model or threshold change occurs from a single override; promotion requires explicit admin approval and rollback path |

---

## Definition of Done

A deliverable is considered **complete** when ALL of the following conditions are met:

1. **Acceptance criteria satisfied:** The deliverable passes its associated acceptance criterion as measured by the defined measurement method, meeting or exceeding the stated target.

2. **Unit tests pass:** All unit tests covering the deliverable's code pass with no failures. Code coverage for the deliverable's modules meets or exceeds 80%.

3. **Integration tests pass:** End-to-end integration tests that exercise the deliverable in conjunction with dependent services pass without failures.

4. **Code review approved:** At least one team member (not the author) has reviewed and approved the code via GitHub pull request review.

5. **Documentation complete:** Public-facing functions and classes have docstrings. Any new API endpoints are documented in the OpenAPI schema. Any user-visible features are documented in the user guide.

6. **No critical bugs open:** No known bugs of severity Critical or High remain open for the deliverable.

7. **Merged to main branch:** The implementation is merged into the `main` branch via a reviewed pull request.

---

## Acceptance Criteria by Phase

### Phase 1 — Infrastructure and Pipeline Core
Primary criteria: AC-009, AC-010, AC-013

### Phase 2 — Agent Implementation
Primary criteria: AC-001, AC-002, AC-004, AC-005

### Phase 3 — Dashboard and Frontend
Primary criteria: AC-003, AC-011, AC-014, AC-015

### Phase 4 — Reporting & Refinement
Primary criteria: AC-006, AC-007, AC-012

### Phase 5 — Delivery & Core Features
Primary criteria: AC-008, AC-016, AC-017

---

## Non-Acceptance Conditions

The following conditions will result in a deliverable being rejected:

- Pipeline crashes (unhandled exception) on any supported input format.
- Dashboard displays stale or incorrect data (results from a different session).
- Agent log is missing or empty for a completed pipeline run.
- Docker Compose fails to start any required service.
- Any hardcoded credentials or API keys present in the repository.
- Test coverage below 80% on core pipeline modules.
