# Project Context

## Purpose
ML-Server-Manager is a lightweight multi-node ML workspace & job management system for research groups. It provides:
- Centralized management of distributed ML compute nodes
- Dataset catalog and per-server storage management
- Container-based (Docker) or virtual-env (conda/venv) job execution
- Role-based access control for team collaboration

## Tech Stack

### Backend
- Python 3.12+
- FastAPI + Uvicorn (ASGI server)
- SQLAlchemy + PostgreSQL (SQLite for PoC)
- Celery + Redis (optional, for async tasks)
- Pydantic for data validation

### Frontend
- React 18 + TypeScript
- Ant Design Pro (enterprise admin UI framework)
- Tailwind CSS (utility styling)
- Vite (build tool)
- umi-request / axios (API client)

### Infrastructure
- Docker + docker-compose
- Master-Worker architecture with REST API communication

## Project Conventions

### Code Style
- **Backend**: PEP 8, type hints, Pydantic models for all API schemas
- **Frontend**: ESLint + Prettier, strict TypeScript, functional components + hooks
- **Naming**: 
  - Python: snake_case for variables/functions, PascalCase for classes
  - TypeScript: camelCase for variables/functions, PascalCase for components/types

### Architecture Patterns
- **Backend**: Layered architecture (routers → services → repositories → models)
- **Frontend**: Feature-based directory structure, centralized API client
- **Communication**: RESTful APIs with JSON responses, structured error handling

### Testing Strategy
- Backend: pytest for unit/integration tests, API endpoint coverage
- Frontend: Jest + React Testing Library for component tests
- CI: Automated lint + type-check + tests before merge

### Git Workflow
- Feature branches: `feature/`, `fix/`, `refactor/` prefixes
- Conventional commits encouraged
- PR required for main branch merges
- Keep CHANGELOG updated for releases

## Domain Context
- **Master Node**: Central server providing global view, API gateway, database
- **Worker Node**: Compute server running ML jobs, reports status to master via agent
- **Dataset**: Local storage on each node, metadata synced to master catalog
- **Job**: ML training/inference task, runs in container or virtual environment

## Important Constraints
- Per-server independent storage (no forced shared filesystem)
- Lightweight deployment (minimal dependencies, single docker-compose)
- Support both Docker containers and conda/venv environments
- Must work across network boundaries (secure inter-node communication)

## External Dependencies
- Docker Engine (required on all nodes)
- PostgreSQL (production) or SQLite (development/PoC)
- Redis (optional, for Celery task queue)
- Git provider for version control
