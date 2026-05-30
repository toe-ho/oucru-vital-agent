.PHONY: up down logs migrate seed test lint build dev dev-build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed

test:
	cd backend && pytest -v
	cd frontend && npm test -- --passWithNoTests

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint

build:
	docker compose build

dev:
	docker compose -f docker-compose.yml -f compose.dev.yml up

dev-build:
	docker compose -f docker-compose.yml -f compose.dev.yml up --build

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U oucru -d oucru_db
