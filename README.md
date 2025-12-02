# ML-Server-Manager

A lightweight multi-node ML workspace & job management system for research groups.

## Features

- **Multi-node Management**: Centralized management of master and worker compute nodes
- **Dataset Catalog**: Per-server independent storage with metadata synced to master
- **Job Execution**: Support for Docker containers and conda/venv environments
- **Role-based Access Control**: Superadmin, admin, and member roles
- **Real-time Monitoring**: Node status, job progress, and resource utilization
- **API Documentation**: Auto-generated Swagger/OpenAPI documentation
- **Type-safe Frontend**: Auto-generated TypeScript API client from OpenAPI spec

## Tech Stack

### Backend
- Python 3.12+ with FastAPI
- SQLAlchemy + PostgreSQL (SQLite for development)
- JWT-based authentication
- Celery + RabbitMQ for async tasks
- uv for fast Python package management
- ruff for linting and formatting

### Frontend
- React 18 + TypeScript
- Ant Design Pro (enterprise admin UI)
- Vite build tool
- Tailwind CSS
- ESLint + Prettier for code quality
- @hey-api/openapi-ts for API client generation

### Worker Agent
- Python 3.12+ with httpx
- Async heartbeat and status reporting
- System resource monitoring (CPU, memory, GPU, storage)

## Quick Start

### Development Setup

#### Backend

```bash
cd backend

# Install uv (if not installed)
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies and run
uv sync
cp ../.env.example .env  # Configure environment
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open http://localhost:5173 in your browser.

#### Worker Agent

```bash
cd worker_agent
uv sync
uv run python agent.py
```

### Code Quality

#### Backend (Python)
```bash
cd backend
uv run ruff check .      # Lint code
uv run ruff format .     # Format code
```

#### Frontend (TypeScript/React)
```bash
cd frontend
pnpm type-check          # TypeScript type checking
pnpm lint                # Run ESLint
pnpm lint:fix            # Run ESLint with auto-fix
pnpm format              # Format with Prettier
pnpm format:check        # Check formatting
pnpm generate:api        # Generate TypeScript API client from OpenAPI spec
```

### Production Deployment

```bash
# Configure environment
cp .env.example .env
# Edit .env with production settings (especially SECRET_KEY)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Project Structure

```
/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes (auth, users, nodes, datasets, jobs)
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # SQLAlchemy models
│   │   └── schemas/        # Pydantic schemas with OpenAPI docs
│   ├── main.py             # Application entry point
│   ├── pyproject.toml      # Python dependencies (uv)
│   └── ruff.toml           # Ruff linter config
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/generated/  # Auto-generated TypeScript API client
│   │   ├── layouts/        # Layout components (ProLayout)
│   │   ├── pages/          # Page components (Dashboard, Nodes, etc.)
│   │   └── utils/          # Utilities (API client, auth)
│   ├── openapi-ts.config.ts # OpenAPI codegen configuration
│   ├── package.json
│   └── vite.config.ts
├── worker_agent/           # Worker node agent
│   ├── agent.py            # Main agent script
│   ├── pyproject.toml      # Python dependencies (uv)
│   └── Dockerfile
├── openspec/               # Spec-driven development
│   ├── changes/            # Change proposals
│   └── specs/              # Current specifications
├── .github/workflows/      # CI workflows (frontend/backend quality checks)
├── docker-compose.yml      # Production deployment (includes RabbitMQ)
├── .env.example            # Environment template
└── AGENTS.md               # Project specification
```

## API Documentation

When running the backend, comprehensive API documentation is available at:
- **Swagger UI**: http://localhost:8000/api/docs - Interactive API explorer
- **ReDoc**: http://localhost:8000/api/redoc - Alternative documentation view
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json - Raw OpenAPI spec

### TypeScript API Client

The frontend uses auto-generated TypeScript types from the OpenAPI spec:

```bash
# Ensure backend is running first
cd frontend
pnpm generate:api
```

This generates typed API client code in `src/api/generated/`.

## Default Credentials

For development, you can register a new user via the API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "adminpass123", "role": "superadmin"}'
```

## CI/CD

GitHub Actions workflows are configured for:
- **Backend Quality** (`.github/workflows/backend-quality.yml`): Runs on `backend/**` changes
  - Python linting with ruff
  - Code formatting check
- **Frontend Quality** (`.github/workflows/frontend-quality.yml`): Runs on `frontend/**` changes
  - TypeScript type checking
  - ESLint linting
  - Prettier formatting check

## License

MIT
