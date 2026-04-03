# 07 — Non-Functional Requirements

[← Back to Index](00-index.md)

---

## Overview

This document specifies the non-functional requirements (NFRs) for the **Agentic AI for High-Frequency Data Quality Monitoring** system. These requirements define the quality attributes the system must satisfy beyond functional correctness. Each requirement includes a measurable target metric.

Priority levels follow MoSCoW: **Must** (mandatory), **Should** (high value), **Could** (nice to have).

> **Note:** NFRs below are team-proposed targets. Items marked with † are engineering best practices beyond original OUCRU requirements, which specify relaxed privacy for anonymous waveform data.

---

## Requirements Table

| ID | Category | Requirement | Target Metric | Priority |
|---|---|---|---|---|
| NFR-001 | Performance | SQI computation latency per 30-second segment shall not exceed the specified limit under normal load conditions. | < 5 seconds per segment | Must |
| NFR-002 | Performance | End-to-end agent pipeline latency for a 1-hour ECG recording (120 × 30s segments) shall not exceed the specified limit, including preprocessing, SQI computation, classification, and report generation. | < 10 minutes total | Must |
| NFR-003 | Performance | The web dashboard (Quality Dashboard and Monitoring Screen) shall achieve full interactive load within the specified limit on a standard broadband connection (≥ 10 Mbps). | < 3 seconds initial load | Must |
| NFR-004 | Performance | All REST API endpoints shall return a response (including error responses) within the specified limit at the 95th percentile under normal load. | < 500 ms (p95) | Must |
| NFR-005 | Performance | Report generation (PDF or HTML) for a single recording shall complete within the specified limit after being triggered. | < 30 seconds | Must |
| NFR-006 | Scalability | The system shall handle concurrent processing of at least the specified number of recordings without degradation in per-recording processing time exceeding 20%. *Aspirational target — initial phase uses sample offline recordings.* | ≥ 50 concurrent recordings | Should |
| NFR-007 | Scalability | The database and storage layer shall support a growing volume of recordings and SQI results without schema changes, targeting at least the specified total recording count without performance degradation on list/query operations. *Aspirational target — initial phase uses sample offline recordings.* | ≥ 100,000 recordings | Should |
| NFR-008 | Scalability | The backend processing pipeline shall be designed for horizontal scaling, allowing additional worker instances to be added without application code changes (stateless workers consuming from a task queue). | Linear throughput scaling with worker count | Should |
| NFR-009 | Reliability | The system shall maintain the specified minimum uptime availability, measured over any rolling 30-day period, excluding planned maintenance windows communicated ≥ 24 hours in advance. | ≥ 99.5% uptime | Must |
| NFR-010 | Reliability | If the LLM API (agent brain) becomes unavailable, the system shall degrade gracefully by falling back to pure rule-based SQI threshold classification, completing the pipeline without agent reasoning, and notifying the user of the degraded mode. | Zero data loss on LLM failure; rule-based fallback activates within 15 seconds | Must |
| NFR-011 | Reliability | The system shall automatically retry failed processing tasks (network errors, transient vital_sqi failures) using exponential backoff before marking a job as failed. | Up to 3 retries; max backoff 60 seconds | Must |
| NFR-012 | Reliability | The system shall guarantee data integrity of uploaded recordings: once a file is accepted and stored, its contents shall not be modified or lost due to system errors. File checksums (SHA-256) shall be verified on storage write and read. | 0 silent data corruption events | Must |
| NFR-013 † | Security | All API endpoints shall require authentication via JWT (JSON Web Token) bearer tokens. Unauthenticated requests shall return HTTP 401. †Team-proposed — original requirements specify relaxed privacy for anonymous, non-PII waveform data. Authentication scope to be confirmed with OUCRU. | 100% endpoint coverage | Must |
| NFR-014 † | Security | All data at rest (uploaded recordings, SQI results, reports) shall be encrypted using AES-256 or equivalent. †Team-proposed — original requirements specify relaxed privacy for anonymous, non-PII waveform data. Authentication scope to be confirmed with OUCRU. | AES-256 encryption at rest | Must |
| NFR-015 † | Security | The system shall implement role-based access control (RBAC) with at least three roles: Admin (full access), Researcher (upload, view, report), Viewer (read-only). Users shall not be able to access recordings or reports outside their assigned permissions. †Team-proposed — original requirements specify relaxed privacy for anonymous, non-PII waveform data. Authentication scope to be confirmed with OUCRU. | 0 unauthorized cross-user data access | Must |
| NFR-016 † | Security | The system shall maintain an immutable audit log of all security-relevant events: user logins, file uploads, configuration changes, report downloads, and role changes, with timestamp and user ID. †Team-proposed — original requirements specify relaxed privacy for anonymous, non-PII waveform data. Authentication scope to be confirmed with OUCRU. | 100% audit coverage for listed event types | Must |
| NFR-017 | Usability | The system shall be operable by a Clinical Researcher with no signal processing or software engineering background, using only the web dashboard and provided onboarding documentation. | New user completes first upload-to-report workflow in < 1 hour without assistance | Must |
| NFR-018 | Usability | The user interface shall minimize required training time by using clear labels, contextual tooltips for all SQI metrics, and a guided workflow for first-time users. | ≤ 1 hour to proficiency for non-technical users | Must |
| NFR-019 | Usability | The web dashboard shall conform to WCAG 2.1 Level AA accessibility guidelines, including sufficient color contrast, keyboard navigability, and screen reader compatibility. | WCAG 2.1 AA compliant | Should |
| NFR-020 | Usability | The dashboard layout shall be fully functional and visually coherent on desktop (≥ 1280px wide) and tablet (768px – 1279px wide) screen sizes. Mobile (< 768px) is out of scope for v1. | Desktop + tablet responsive; no horizontal scroll | Must |
| NFR-021 | Maintainability | The codebase shall follow a modular architecture with clear separation between: data ingestion, signal processing, agent orchestration, reporting, and API layers. No direct cross-layer dependencies shall exist outside of defined interfaces. | Dependency rule violations = 0 in CI check | Must |
| NFR-022 | Maintainability | All public functions, classes, API endpoints, and agent tools shall have documentation coverage at or above the specified threshold, enforced in CI. | ≥ 80% documentation coverage | Should |
| NFR-023 | Maintainability | The SQI metric catalog and agent tool registry shall be extensible: adding a new SQI metric or agent tool shall require changes only to the metric/tool definition file and its registration, with no changes to core pipeline code. | New metric/tool addable in < 1 day engineering effort | Must |
| NFR-024 | Maintainability | All REST API endpoints shall be documented using OpenAPI 3.0 (Swagger), with a live interactive specification available at `/api/docs` in development and staging environments. | 100% endpoint coverage in OpenAPI spec | Must |

---

## NFR Verification Methods

| Category | Primary Verification Method |
|---|---|
| Performance | Automated load tests (k6 or Locust) run in CI on staging environment |
| Scalability | Horizontal scaling smoke test with simulated concurrent job queue |
| Reliability | Chaos engineering: LLM API mock failure, database disconnection test |
| Security | Static analysis (SAST), penetration test checklist, JWT validation unit tests |
| Usability | Moderated usability session with 2–3 Clinical Researcher representatives |
| Maintainability | CI linting gates, documentation coverage report, architecture dependency check |

---

## Notes

- Performance targets are defined for **staging environment** hardware equivalent to production. Results on developer laptops are informational only.
- NFR-010 (graceful degradation) is considered a hard safety requirement given the clinical context: a failure in the AI layer must never prevent access to raw quality data.
- NFR-015 (RBAC) scope is limited to v1 roles. Fine-grained per-study or per-patient permissions are deferred to a future release.
