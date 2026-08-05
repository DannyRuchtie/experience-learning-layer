.PHONY: install db-up db-down migrate test lint typecheck run

install:
	pip install -e ".[dev]"

db-up:
	docker compose up -d

db-down:
	docker compose down

migrate:
	alembic upgrade head

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ apps/

typecheck:
	mypy src/ apps/

run:
	uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
