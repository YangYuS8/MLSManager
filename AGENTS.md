<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Project: ML‑Server‑Manager

## Overview
This repository implements a lightweight multi‑node / per‑server ML‑workspace & job‑management system for research groups:
- Backend: API server, node registry, dataset catalog, job & container management, metadata & audit logs.
- Frontend: Admin / User panel for dataset browsing / server‑node view / job submission / status monitoring / logs / user & permission management.
- Supports per‑server independent storage (each server stores its own datasets / projects / outputs), no forced shared network storage.
- Supports container‑based (Docker) environment or virtual‑env (conda/venv) — users can select.
- Supports multiple servers: a central “master” node + multiple “worker / compute” nodes. Master node provides global view; worker nodes report dataset & job status to master.
- Easy deployment: uses Docker + docker‑compose; minimal dependencies; one‑click (or simple script) setup; lightweight resource footprint; easy for team to maintain or hand over.

## Tech Stack / Dependencies
- Backend:
  - Python 3.12+  
  - FastAPI + Uvicorn (ASGI server) — supports async, high performance, hot‑reload during development. :contentReference[oaicite:5]{index=5}  
  - ORM / database layer: SQLAlchemy (or equivalent) + PostgreSQL (or SQLite for PoC)  
  - Optional: Task queue / background jobs (e.g. Celery + RabbitMQ) — for asynchronous tasks: dataset import/download, container launch, job monitoring, inter‑node communication, metadata sync  
- Frontend:
  - React 18 + TypeScript  
  - UI framework: Ant Design Pro (enterprise-level admin UI solution with built-in layouts, access control, and i18n)  
  - Utility CSS: Tailwind CSS (for custom styling supplements)  
  - Build tool: Vite (fast cold start, instant HMR, optimized builds)  
- Deployment / Containerization:
  - Docker + docker‑compose  
  - Each “node” (master or worker) runs Docker; worker nodes run a lightweight “agent” that communicates with master via REST API / secure channel to report status / dataset registry / accept commands  
- Configuration:
  - Environment variables (e.g. `.env` or config file) for DB settings / secret keys / node identification / network config  
- Logging & Audit:
  - Structured logging (API calls, job submissions, container status, dataset operations) + persistent storage of logs / metadata / audit information  

## Development / Build / Run Commands

### Local Development (Recommended)

```bash
# Step 1: Start infrastructure services
make services-up      # start db + rabbitmq in background

# Step 2: Run components locally with hot-reload (in separate terminals)
make local-backend    # backend with uvicorn --reload
make local-frontend   # frontend with vite dev
make local-worker     # worker with air hot-reload
```

### Full-Stack Docker Development

```bash
make dev              # start all services with docker-compose (hot-reload)
make dev-up           # start in background
make dev-down         # stop services
make dev-logs         # view logs
make dev-build        # rebuild images (use HTTP_PROXY=... for proxy)
```

### Frontend Commands

```bash
cd frontend  
pnpm install  
pnpm dev              # for development (hot reload)  
pnpm build            # build for production
pnpm type-check       # TypeScript type checking
pnpm lint             # run ESLint
pnpm lint:fix         # run ESLint with auto-fix
pnpm format           # format code with Prettier
pnpm format:check     # check formatting without changes
pnpm generate:api     # generate TypeScript API client from OpenAPI spec
```

### Backend Commands

```bash
cd backend
uv sync               # install dependencies
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
uv run ruff check .   # lint Python code
uv run ruff format .  # format Python code
```

### Worker Agent Commands (Go)

```bash
cd worker_agent
go mod download       # install dependencies
go run ./cmd/agent    # run agent
go build -o agent ./cmd/agent  # build binary

# With hot-reload (requires air)
go install github.com/air-verse/air@latest
air                   # run with hot-reload
```

### Production Deployment

```bash
make prod             # start production environment
make prod-up          # start in background
make prod-down        # stop services
make prod-build       # build production images
```

## Project Structure (suggested)

```
/                  # project root
  /backend/         # FastAPI + API + job & node logic + database / ORM + agent interface
  /frontend/        # React + TS + Ant Design + Tailwind + UI components / pages
  /worker_agent/    # Go-based worker node agent: dataset scan / metadata report / job launch / status sync
  /infra/           # docker‑compose files, deployment / startup / registration scripts, configs, .env.example
  /docs/            # design docs, architecture diagrams, usage guides, README, CONTRIBUTING, etc.
  Makefile          # unified development commands
  AGENTS.md          # this file — project spec / tech stack / conventions / guidelines
  .env.example       # template environment configuration
```

## Coding Conventions & Style Guide

- **Backend**:
  - Use Pydantic (if FastAPI) for request/response schemas & data validation
  - Follow consistent logging & error‑handling convention; all API errors should return structured JSON with error codes / messages
  - Use migrations for database schema changes (e.g. Alembic) if using Postgres / SQLAlchemy
- **Frontend**:
  - Use React 18 functional components + hooks + TS + strict typing
  - Use Ant Design Pro components and layouts (ProLayout, ProTable, ProForm, etc.) + Tailwind for custom styling / layout tweaks
  - Leverage Ant Design Pro's built-in access control, routing configuration, and i18n capabilities
  - Keep API communication via a central "API client" module (fetch / axios / umi-request) + typed interfaces / types
  - Organize pages / components in feature‑based directory structure (e.g. `pages/datasets`, `pages/jobs`, `components/ui`, etc.)

## Testing & Quality Assurance (optional but recommended)

- Frontend: unit tests + component tests (e.g. Jest + React Testing Library) + type‑checking (TS) + lint (eslint / prettier)
- Backend: unit tests + integration tests for API endpoints + possibly container / job management tests + database tests
- CI (optional): automated tests + lint + build before merge / deploy

## Deployment & Maintenance Notes

- Master node services run via docker‑compose; for production you may add reverse‑proxy (e.g. nginx), TLS / HTTPS, firewall / access control as needed
- Worker nodes register with master via secure channel (token / secret / key); communication should be authenticated & encrypted (HTTPS / VPN / SSH tunnel / similar) if across network / internet
- Environment variables for secrets / configs; do **not** commit `.env` to repo — use `.env.example` as template
- Provide upgrade / migration guide: when backend / API changes / DB schema evolves, run migrations / update containers / rebuild images; keep backward compatibility when possible

## Security & Permissions

- Authentication & authorization: role‑based access control (RBAC) — e.g. superadmin / admin / member
- Restrict sensitive operations (dataset delete / migration / node removal / global config) to admins / superadmins
- Sanitize and validate all user inputs (especially paths / filenames / URLs / dataset import URLs) to avoid injection / path‑traversal / command‑injection
- If exposing UI / API over network: enforce HTTPS, secure credentials, limit allowed hosts / origins, use secure cookies / tokens, rate‑limit where appropriate

## Contributing / Workflow Guidelines

- Use Git + branch + pull‑request workflow
- Write clear commit messages; update docs / schema / migration when changing API / data model / behavior
- Before merging: run tests + lint + ensure build passes + review changes in API / job logic / security-sensitive code
- Maintain CHANGELOG / version tags / release notes
