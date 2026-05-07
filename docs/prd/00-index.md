# Agentic AI for High-Frequency Data Quality Monitoring — PRD Index

## Version History

| Version | Date       | Author        | Description   |
|---------|------------|---------------|---------------|
| 1.0     | 2026-04-03 | OUCRU Capstone Team | Initial Draft |

---

## Project Summary

OUCRU (Oxford University Clinical Research Unit) operates Electronic Data Capture (EDC) systems that continuously collect high-frequency physiological waveform data — ECG and PPG signals — from wearable devices and bedside monitors deployed in clinical research settings. Current quality control relies on static rule-based checks and periodic manual review by data engineers and clinical researchers; this approach does not scale with growing data volume, velocity, and source heterogeneity. This project builds an **agentic AI system** that autonomously monitors waveform data quality by orchestrating OUCRU's existing signal quality tools, exposing results through a web dashboard designed for medical practitioners, and generating automated quality reports — replacing slow, expensive manual review with intelligent assessment. Imaging data quality is deferred to future phases; the current scope focuses exclusively on waveform data (ECG, PPG).

---

## Table of Contents

### Overview

| # | File | Description |
|---|------|-------------|
| 01 | [overview/01-executive-summary.md](overview/01-executive-summary.md) | One-page executive summary: problem, solution, deliverables, success metrics |
| 02 | [overview/02-problem-statement.md](overview/02-problem-statement.md) | Detailed problem analysis, pain points, cost of failure |
| 03 | [overview/03-goals-and-non-goals.md](overview/03-goals-and-non-goals.md) | Project goals and non-goals |
| 04 | [overview/04-user-personas.md](overview/04-user-personas.md) | User personas: clinical researcher, data engineer, study coordinator |

### Requirements

| # | File | Description |
|---|------|-------------|
| 01 | [requirements/01-user-stories.md](requirements/01-user-stories.md) | User stories and primary use case flows |
| 02 | [requirements/02-functional-requirements.md](requirements/02-functional-requirements.md) | Functional requirements by system component |
| 03 | [requirements/03-non-functional-requirements.md](requirements/03-non-functional-requirements.md) | Performance, reliability, security, and scalability requirements |
| 04 | [requirements/04-acceptance-criteria.md](requirements/04-acceptance-criteria.md) | Acceptance criteria and definition of done |

### Architecture

| # | File | Description |
|---|------|-------------|
| 01 | [architecture/01-system-architecture.md](architecture/01-system-architecture.md) | High-level architecture, component diagram, data flow |
| 02 | [architecture/02-agent-design.md](architecture/02-agent-design.md) | Agentic AI design: LLM selection, tool registry, orchestration logic |
| 03 | [architecture/03-api-specifications.md](architecture/03-api-specifications.md) | REST API endpoints, request/response schemas |
| 04 | [architecture/04-data-model.md](architecture/04-data-model.md) | Data models, database schema, storage strategy |
| 05 | [architecture/05-tech-stack.md](architecture/05-tech-stack.md) | Full technology stack with justifications |

### Product Design

| # | File | Description |
|---|------|-------------|
| 01 | [product-design/01-ui-ux-specifications.md](product-design/01-ui-ux-specifications.md) | Web dashboard UI/UX design, component specifications |

### Delivery

| # | File | Description |
|---|------|-------------|
| 01 | [delivery/01-development-phases.md](delivery/01-development-phases.md) | Development phases, milestones, and delivery timeline |
| 02 | [delivery/02-risk-assessment.md](delivery/02-risk-assessment.md) | Risk register and mitigation strategies |
| 03 | [delivery/03-testing-strategy.md](delivery/03-testing-strategy.md) | Unit, integration, and end-to-end testing strategy |

### Appendix

| # | File | Description |
|---|------|-------------|
| 01 | [appendix/01-appendix.md](appendix/01-appendix.md) | Appendix: glossary, references, supplementary material |
