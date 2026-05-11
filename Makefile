.PHONY: help up down build migrate seed logs \
        test test-backend test-frontend test-local \
        lint format pull-model

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  up              Start all services (Docker Compose)"
	@echo "  down            Stop all services"
	@echo "  build           Rebuild Docker images"
	@echo "  migrate         Run Alembic migrations inside backend container"
	@echo "  seed            Seed default settings into the database"
	@echo "  logs            Tail all service logs"
	@echo ""
	@echo "  test            Run all tests (backend + frontend) in Docker"
	@echo "  test-backend    Run backend tests in Docker with coverage"
	@echo "  test-frontend   Run frontend tests locally"
	@echo "  test-local      Run backend tests locally (requires local venv)"
	@echo ""
	@echo "  lint            Lint backend (ruff) and frontend (eslint)"
	@echo "  format          Auto-format backend with ruff"
	@echo "  pull-model      Pull the Ollama model into the running container"

# ── Docker lifecycle ──────────────────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# ── Database ──────────────────────────────────────────────────────────────────
migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -c "from app.db.init_db import seed_db; import asyncio; asyncio.run(seed_db())"

# ── Tests ─────────────────────────────────────────────────────────────────────
test: test-backend test-frontend

test-backend:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing --ignore=tests/performance

test-frontend:
	cd frontend && npm test -- --run

test-local:
	cd backend && pytest tests/ -v --cov=app --cov-report=html --ignore=tests/performance

# ── Code quality ─────────────────────────────────────────────────────────────
lint:
	cd backend && ruff check app/ tests/
	cd frontend && npx eslint .

format:
	cd backend && ruff format app/ tests/

# ── Ollama ────────────────────────────────────────────────────────────────────
pull-model:
	docker compose exec ollama ollama pull qwen3:8b
