# Change: Infrastructure Improvements - uv, RabbitMQ, Node 22

## Why
1. Backend `uv sync` fails because `pyproject.toml` references a non-existent `README.md` file
2. Worker agent should use uv for consistency with backend
3. RabbitMQ is more robust than Redis for task queues (better message persistence, acknowledgments)
4. Node.js 22 is the current LTS version with better performance

## What Changes
- **Backend**: Remove `readme` field from pyproject.toml to fix `uv sync` error
- **Worker Agent**: Convert from requirements.txt to uv/pyproject.toml
- **Task Queue**: Replace Redis with RabbitMQ (Celery broker change)
- **Frontend Dockerfile**: Upgrade from Node 20 to Node 22

## Impact
- Affected code:
  - `backend/pyproject.toml` - Remove readme field
  - `worker_agent/pyproject.toml` - New file (uv migration)
  - `worker_agent/requirements.txt` - To be removed
  - `worker_agent/Dockerfile` - Update to use uv
  - `docker-compose.yml` - Replace redis with rabbitmq service
  - `frontend/Dockerfile` - Change base image to node:22-alpine
  - `backend/app/core/config.py` - Update broker URL config
