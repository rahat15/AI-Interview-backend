.PHONY: help build up down restart logs clean test quality migrate seed demo

help: ## Show this help message
	@echo "Interview Coach API - Development Commands"
	@echo "=========================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start the development stack
	docker-compose up -d

down: ## Stop the development stack
	docker-compose down

restart: ## Restart the development stack
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-db: ## Show database logs
	docker-compose logs -f postgres

clean: ## Clean up containers, volumes, and images
	docker-compose down -v --rmi all
	docker system prune -f

test: ## Run tests
	docker-compose exec api pytest

test-cov: ## Run tests with coverage
	docker-compose exec api pytest --cov=apps --cov=core --cov=interview --cov-report=html

test-watch: ## Run tests in watch mode
	docker-compose exec api pytest --watch

quality: ## Run all code quality checks
	docker-compose exec api black --check .
	docker-compose exec api isort --check-only .
	docker-compose exec api flake8 .
	docker-compose exec api mypy .

format: ## Format code
	docker-compose exec api black .
	docker-compose exec api isort .

migrate: ## Run database migrations
	docker-compose exec api alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MESSAGE="description")
	docker-compose exec api alembic revision --autogenerate -m "$(MESSAGE)"

migrate-rollback: ## Rollback last migration
	docker-compose exec api alembic downgrade -1

seed: ## Seed demo data
	docker-compose exec api python -m scripts.seed_demo

shell: ## Open shell in API container
	docker-compose exec api bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d interview_coach

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

health: ## Check service health
	@echo "Checking API health..."
	@curl -s http://localhost:8080/healthz || echo "API not responding"
	@echo "Checking database..."
	@docker-compose exec -T postgres pg_isready -U postgres || echo "Database not ready"
	@echo "Checking Redis..."
	@docker-compose exec -T redis redis-cli ping || echo "Redis not responding"

dev-setup: ## Complete development setup
	@echo "Setting up development environment..."
	make build
	make up
	@echo "Waiting for services to be ready..."
	@sleep 10
	make migrate
	make seed
	@echo "Development environment ready!"
	@echo "API: http://localhost:8080"
	@echo "Docs: http://localhost:8080/docs"
	@echo "Health: http://localhost:8080/healthz"

reset: ## Reset everything and start fresh
	make clean
	make dev-setup
