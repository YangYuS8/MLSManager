# Implementation Tasks

## 1. Fix Backend uv sync Error
- [x] 1.1 Remove `readme = "README.md"` from `backend/pyproject.toml`
- [x] 1.2 Add `tool.hatch.build.targets.wheel` config

## 2. Worker Agent: Migrate to uv
- [x] 2.1 Create `worker/pyproject.toml` with dependencies
- [x] 2.2 Create `worker/ruff.toml` for linting config
- [x] 2.3 Create `worker/Dockerfile` to use uv
- [x] 2.4 Remove `worker/requirements.txt`

## 3. Replace Redis with RabbitMQ
- [x] 3.1 Update `docker-compose.yml` - replace redis service with rabbitmq
- [x] 3.2 Update `backend/app/core/config.py` - change broker URL to AMQP
- [x] 3.3 Update `backend/pyproject.toml` - remove redis, add celery AMQP transport

## 4. Frontend: Upgrade to Node 22
- [x] 4.1 Update `frontend/Dockerfile` - change `node:20-alpine` to `node:22-alpine`

## 5. Documentation
- [x] 5.1 Update `AGENTS.md` with new dependencies info and worker commands
