"""ML-Server-Manager Backend Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db

# OpenAPI Tags metadata
tags_metadata = [
    {
        "name": "auth",
        "description": "Authentication operations: login, register, token management",
    },
    {
        "name": "users",
        "description": "User management operations (admin-only for most endpoints)",
    },
    {
        "name": "nodes",
        "description": "Compute node registration, monitoring, and heartbeat management",
    },
    {
        "name": "datasets",
        "description": "Dataset catalog: register, browse, and manage datasets across nodes",
    },
    {
        "name": "jobs",
        "description": "Job submission, monitoring, and lifecycle management",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Node Type: {settings.node_type}, Node ID: {settings.node_id}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## ML-Server-Manager API

Lightweight multi-node ML workspace & job management system for research groups.

### Features
- **Multi-node support**: Central master node + multiple worker/compute nodes
- **Dataset catalog**: Per-server independent storage with centralized metadata
- **Job management**: Submit, monitor, and manage ML training jobs
- **Container support**: Docker-based or conda/venv environments
- **User management**: Role-based access control (superadmin/admin/member)

### Authentication
Most endpoints require Bearer token authentication. Use `/api/v1/auth/login` to obtain a token.
""",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "ML-Server-Manager Team",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "node_type": settings.node_type,
        "node_id": settings.node_id,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
