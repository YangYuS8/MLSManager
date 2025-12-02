# Worker Agent Dockerfile using uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy the project into the image
COPY . .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Set environment variables
ENV AGENT_MASTER_URL=http://backend:8000
ENV AGENT_NODE_ID=worker-001
ENV AGENT_HEARTBEAT_INTERVAL=30
ENV AGENT_STORAGE_PATH=/data

# Create data directory
RUN mkdir -p /data

# Run the agent
CMD ["uv", "run", "python", "agent.py"]
