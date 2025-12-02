.PHONY: help dev dev-up dev-down dev-logs dev-logs-backend dev-logs-frontend \
        prod prod-up prod-down prod-logs prod-build \
        clean clean-volumes dev-build

# Proxy settings (override with: make dev-build HTTP_PROXY=http://... HTTPS_PROXY=http://...)
HTTP_PROXY ?=
HTTPS_PROXY ?=

# Default target
help:
	@echo "ML-Server-Manager Development Commands"
	@echo ""
	@echo "Development Environment (hot-reload):"
	@echo "  make dev              - Start development environment"
	@echo "  make dev-up           - Start dev containers in background"
	@echo "  make dev-down         - Stop development environment"
	@echo "  make dev-build        - Build dev images (use HTTP_PROXY=... for proxy)"
	@echo "  make dev-logs         - View all dev container logs"
	@echo "  make dev-logs-backend - View backend logs only"
	@echo "  make dev-logs-frontend- View frontend logs only"
	@echo "  make dev-logs-db      - View database logs only"
	@echo ""
	@echo "Production Environment:"
	@echo "  make prod             - Start production environment"
	@echo "  make prod-up          - Start prod containers in background"
	@echo "  make prod-down        - Stop production environment"
	@echo "  make prod-logs        - View all prod container logs"
	@echo "  make prod-build       - Build production images"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Stop all containers and remove images"
	@echo "  make clean-volumes    - Remove all volumes (WARNING: deletes data)"
	@echo ""
	@echo "Proxy usage example:"
	@echo "  make dev-build HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897"

# ==================== Development Environment ====================

dev:
	docker compose -f docker-compose.dev.yml up

dev-up:
	docker compose -f docker-compose.dev.yml up -d

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-build:
	HTTP_PROXY=$(HTTP_PROXY) HTTPS_PROXY=$(HTTPS_PROXY) docker compose -f docker-compose.dev.yml build

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-logs-backend:
	docker compose -f docker-compose.dev.yml logs -f backend

dev-logs-frontend:
	docker compose -f docker-compose.dev.yml logs -f frontend

dev-logs-db:
	docker compose -f docker-compose.dev.yml logs -f db

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
