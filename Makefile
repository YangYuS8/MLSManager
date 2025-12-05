.PHONY: help \
        dev dev-up dev-down dev-logs dev-logs-backend dev-logs-frontend dev-build dev-restart \
        local local-backend local-frontend local-worker services services-up services-down services-logs \
        prod prod-up prod-down prod-logs prod-build \
        clean clean-volumes

# Load environment variables from .env.dev for local development
# Note: These are defaults, can be overridden by command line
-include .env.dev
export

# Default target
help:
	@echo "ML-Server-Manager Development Commands"
	@echo ""
	@echo "=== Local Development (Hot-Reload) ==="
	@echo "  make services         - Start only db + rabbitmq (Docker)"
	@echo "  make services-up      - Start services in background"
	@echo "  make services-down    - Stop services"
	@echo "  make local-backend    - Run backend locally with hot-reload (requires services)"
	@echo "  make local-frontend   - Run frontend locally with hot-reload"
	@echo "  make local-worker     - Run worker locally with hot-reload (requires services)"
	@echo ""
	@echo "=== Docker Development (Full Stack) ==="
	@echo "  make dev              - Start full development environment"
	@echo "  make dev-up           - Start dev containers in background"
	@echo "  make dev-down         - Stop development environment"
	@echo "  make dev-build        - Build dev images (use HTTP_PROXY=... for proxy)"
	@echo "  make dev-logs         - View all dev container logs"
	@echo "  make dev-logs-backend - View backend logs only"
	@echo "  make dev-logs-frontend- View frontend logs only"
	@echo "  make dev-logs-db      - View database logs only"
	@echo "  make dev-logs-worker  - View worker logs only"
	@echo ""
	@echo "=== Production Environment ==="
	@echo "  make prod             - Start production environment"
	@echo "  make prod-up          - Start prod containers in background"
	@echo "  make prod-down        - Stop production environment"
	@echo "  make prod-logs        - View all prod container logs"
	@echo "  make prod-build       - Build production images"
	@echo ""
	@echo "=== Cleanup ==="
	@echo "  make clean            - Stop all containers and remove images"
	@echo "  make clean-volumes    - Remove all volumes (WARNING: deletes data)"
	@echo ""
	@echo "Environment variables are loaded from .env.dev (local dev) or .env (production)"

# ==================== Local Development (Hot-Reload) ====================

# Start only infrastructure services (db + rabbitmq)
services:
	docker compose -f docker-compose.dev.yml up db rabbitmq

services-up:
	docker compose -f docker-compose.dev.yml up -d db rabbitmq

services-down:
	docker compose -f docker-compose.dev.yml stop db rabbitmq

services-logs:
	docker compose -f docker-compose.dev.yml logs -f db rabbitmq

# Local backend with hot-reload (uses DATABASE_URL from .env.dev)
local-backend:
	@echo "Starting backend with hot-reload..."
	@echo "Make sure services are running: make services-up"
	cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Local frontend with hot-reload (uses VITE_API_BASE_URL from .env.dev)
local-frontend:
	@echo "Starting frontend with hot-reload..."
	cd frontend && pnpm dev

# Local worker with hot-reload (uses AGENT_* from .env.dev)
# Requires air: go install github.com/air-verse/air@latest
local-worker:
	@echo "Starting worker agent with hot-reload..."
	@echo "Make sure services are running: make services-up"
	cd worker_agent && \
		AGENT_STORAGE_PATH="$(PWD)/worker_agent/data" \
		AGENT_DATASETS_PATH="$(PWD)/worker_agent/data/datasets" \
		AGENT_TOKEN_FILE="$(PWD)/worker_agent/.ml-agent/token" \
		air

# ==================== Docker Development Environment ====================

dev:
	docker compose -f docker-compose.dev.yml up

dev-up:
	docker compose -f docker-compose.dev.yml up -d

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-build:
	docker compose -f docker-compose.dev.yml build

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-logs-backend:
	docker compose -f docker-compose.dev.yml logs -f backend

dev-logs-frontend:
	docker compose -f docker-compose.dev.yml logs -f frontend

dev-logs-db:
	docker compose -f docker-compose.dev.yml logs -f db

dev-logs-worker:
	docker compose -f docker-compose.dev.yml logs -f worker

dev-restart:
	docker compose -f docker-compose.dev.yml restart

dev-restart-backend:
	docker compose -f docker-compose.dev.yml restart backend

dev-restart-frontend:
	docker compose -f docker-compose.dev.yml restart frontend

# ==================== Production Environment ====================

prod:
	docker compose -f docker-compose.yml up

prod-up:
	docker compose -f docker-compose.yml up -d

prod-down:
	docker compose -f docker-compose.yml down

prod-logs:
	docker compose -f docker-compose.yml logs -f

prod-build:
	docker compose -f docker-compose.yml build

# ==================== Cleanup ====================

clean:
	docker compose -f docker-compose.dev.yml down --rmi local
	docker compose -f docker-compose.yml down --rmi local

clean-volumes:
	docker compose -f docker-compose.dev.yml down -v
	docker compose -f docker-compose.yml down -v
	@echo "WARNING: All volumes have been removed!"
