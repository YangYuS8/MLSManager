## MODIFIED Requirements

### Requirement: Python Package Management
All Python components (backend, worker_agent) SHALL use uv as the package manager for dependency management, virtual environment creation, and script execution.

#### Scenario: Backend dependency sync
- **WHEN** developer runs `uv sync` in backend directory
- **THEN** all dependencies are installed successfully without errors

#### Scenario: Worker agent dependency sync
- **WHEN** developer runs `uv sync` in worker_agent directory
- **THEN** all dependencies are installed successfully

### Requirement: Task Queue Infrastructure
The system SHALL use RabbitMQ as the message broker for Celery task queues.

#### Scenario: Celery broker connection
- **WHEN** backend service starts with Celery enabled
- **THEN** it connects to RabbitMQ using AMQP protocol

#### Scenario: Task message persistence
- **WHEN** a task is submitted and worker is temporarily unavailable
- **THEN** RabbitMQ persists the message until worker acknowledges completion

### Requirement: Frontend Build Environment
The frontend Dockerfile SHALL use Node.js 22 LTS as the base image for building and development.

#### Scenario: Frontend Docker build
- **WHEN** frontend Docker image is built
- **THEN** it uses node:22-alpine as the builder base image
