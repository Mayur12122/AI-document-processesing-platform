.PHONY: help up down restart logs build migrate seed test test-backend test-frontend

help:
	@echo "Intelligent Document Processing Platform Commands:"
	@echo "  make up           Start all Docker Compose services"
	@echo "  make down         Stop all Docker Compose services"
	@echo "  make build        Rebuild all Docker containers"
	@echo "  make logs         Tail logs from all services"
	@echo "  make migrate      Run database migrations (Alembic)"
	@echo "  make seed         Generate synthetic demo data & ingest test documents"
	@echo "  make test         Run backend and frontend tests"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up --build -d

logs:
	docker compose logs -f

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m scripts.generate_demo_documents

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend
