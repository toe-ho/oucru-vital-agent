# Repository Workflow

## Required Reading

Before changing scope or architecture, read:

1. `README.md`
2. `docs/prd/00-index.md`
3. `docs/development-roadmap.md`
4. `docs/code-standards.md`

## Workflow Rules

- Execute work in roadmap order unless the user explicitly reprioritizes.
- Prefer existing plan files in `plans/` over creating replacement plans.
- Keep code files under 200 lines when practical.
- Use Python `snake_case` and TypeScript/React ecosystem conventions.
- Do not commit secrets, patient data, or raw waveform arrays.
- Do not place raw signal arrays in LLM-visible prompts or logs. Use references or summaries.
- Update living docs after meaningful implementation changes.

## Commands

```bash
make up
make down
make lint
make test
docker compose ps
```

## Source of Truth

- Product scope: `docs/prd/`
- Living architecture: `docs/system-architecture.md`
- Delivery status: `docs/development-roadmap.md`
- Change log: `docs/project-changelog.md`

## Implementation Notes

- Backend owns ingestion, persistence, reporting, governance, and grounded chat APIs.
- Frontend consumes backend APIs only; no direct database access.
- Docker Compose is the required local baseline for cross-service validation.
