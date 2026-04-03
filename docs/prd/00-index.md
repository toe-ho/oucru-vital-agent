# Agentic AI for High-Frequency Data Quality Monitoring — PRD Index

## Version History

| Version | Date       | Author        | Description   |
|---------|------------|---------------|---------------|
| 1.0     | 2026-04-03 | OUCRU Capstone Team | Initial Draft |

---

## Project Summary

OUCRU (Oxford University Clinical Research Unit) operates Electronic Data Capture (EDC) systems that continuously collect high-frequency physiological waveform data — ECG and PPG signals — from wearable devices and bedside monitors deployed in clinical research settings. Current quality control relies on static rule-based checks and periodic manual review by data engineers and clinical researchers; this approach does not scale with growing data volume, velocity, and source heterogeneity. This project builds an **agentic AI system** that autonomously monitors waveform data quality by orchestrating OUCRU's existing open-source `vital_sqi` signal quality library, exposing results through a web dashboard designed for medical practitioners, and generating automated quality reports — replacing slow, expensive manual review with intelligent, continuous assessment. Imaging data quality is deferred to future phases; the current scope focuses exclusively on waveform data (ECG, PPG).

---

## Table of Contents

| # | File | Description |
|---|------|-------------|
| 01 | [01-executive-summary.md](01-executive-summary.md) | One-page executive summary: problem, solution, deliverables, success metrics |
| 02 | [02-problem-statement.md](02-problem-statement.md) | Detailed problem analysis, pain points, cost of failure |
| 03 | [03-goals-and-non-goals.md](03-goals-and-non-goals.md) | Project goals and non-goals |
| 04 | [04-user-personas.md](04-user-personas.md) | User personas: clinical researcher, data engineer, study coordinator |
| 05 | [05-user-stories.md](05-user-stories.md) | User stories and primary use case flows |
| 06 | [06-functional-requirements.md](06-functional-requirements.md) | Functional requirements by system component |
| 07 | [07-non-functional-requirements.md](07-non-functional-requirements.md) | Performance, reliability, security, and scalability requirements |
| 08 | [08-system-architecture.md](08-system-architecture.md) | High-level architecture, component diagram, data flow |
| 09 | [09-agent-design.md](09-agent-design.md) | Agentic AI design: LLM selection, tool registry, orchestration logic |
| 10 | [10-api-specifications.md](10-api-specifications.md) | REST API endpoints, request/response schemas |
| 11 | [11-data-model.md](11-data-model.md) | Data models, database schema, storage strategy |
| 12 | [12-ui-ux-specifications.md](12-ui-ux-specifications.md) | Web dashboard UI/UX design, component specifications |
| 13 | [13-tech-stack.md](13-tech-stack.md) | Full technology stack with justifications |
| 14 | [14-development-phases.md](14-development-phases.md) | Development phases, milestones, and delivery timeline |
| 15 | [15-risk-assessment.md](15-risk-assessment.md) | Risk register and mitigation strategies |
| 16 | [16-testing-strategy.md](16-testing-strategy.md) | Unit, integration, and end-to-end testing strategy |
| 17 | [17-acceptance-criteria.md](17-acceptance-criteria.md) | Acceptance criteria and definition of done |
| 18 | [18-appendix.md](18-appendix.md) | Appendix: glossary, references, supplementary material |
