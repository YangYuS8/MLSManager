"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, nodes, datasets, jobs, files, settings, projects

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
