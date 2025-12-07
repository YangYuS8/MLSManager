"""Code-Server API endpoints for project editing."""

import os
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.project import Project

router = APIRouter(prefix="/code-server", tags=["code-server"])


class CodeServerURLResponse(BaseModel):
    """Response model for code-server URL."""

    url: str
    project_name: str
    workspace_path: str


class CodeServerStatusResponse(BaseModel):
    """Response model for code-server status."""

    available: bool
    port: int
    base_url: str


def get_code_server_base_url() -> str:
    """Get the base URL for code-server."""
    port = os.getenv("CODE_SERVER_PORT", "8443")
    # In development, code-server is on localhost
    # In production, this should be configured via environment
    host = os.getenv("CODE_SERVER_HOST", "localhost")
    return f"http://{host}:{port}"


def get_projects_root() -> str:
    """Get the projects root path."""
    return os.getenv("PROJECTS_ROOT_PATH", "./projects")


def validate_project_path(project_path: str) -> bool:
    """
    Validate that the project path is safe and within projects root.
    
    Prevents path traversal attacks.
    """
    projects_root = os.path.realpath(get_projects_root())
    full_path = os.path.realpath(os.path.join(projects_root, project_path))
    return full_path.startswith(projects_root)


@router.get(
    "/status",
    response_model=CodeServerStatusResponse,
    summary="Check code-server status",
    description="Check if code-server is available and get its configuration.",
)
async def get_code_server_status(
    current_user: CurrentUser,
) -> CodeServerStatusResponse:
    """Check code-server availability."""
    port = int(os.getenv("CODE_SERVER_PORT", "8443"))
    base_url = get_code_server_base_url()
    
    # TODO: Add actual health check to code-server
    # For now, just return configuration
    return CodeServerStatusResponse(
        available=True,
        port=port,
        base_url=base_url,
    )


@router.get(
    "/url/{project_id}",
    response_model=CodeServerURLResponse,
    summary="Get code-server URL for project",
    description="""
    Generate a code-server URL for editing a specific project.
    
    The URL will open code-server with the project folder pre-selected.
    User must authenticate with code-server separately (first time only).
    """,
    responses={
        404: {"description": "Project not found"},
        403: {"description": "Access denied to project"},
        400: {"description": "Invalid project path"},
    },
)
async def get_project_editor_url(
    db: DbSession,
    project_id: int,
    current_user: CurrentUser,
) -> CodeServerURLResponse:
    """
    Get the code-server URL for a project.
    
    The returned URL opens code-server with the project folder.
    """
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check access (owner or public project)
    if not project.is_public and project.owner_id != current_user.id:
        # Check if user is admin
        if current_user.role not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )
    
    # Get project path relative to projects root
    # The project's local_path should be relative to PROJECTS_ROOT_PATH
    project_path = project.local_path
    
    # If local_path is absolute, extract relative part
    projects_root = get_projects_root()
    if os.path.isabs(project_path):
        try:
            project_path = os.path.relpath(project_path, projects_root)
        except ValueError:
            # On Windows, relpath can fail across drives
            project_path = os.path.basename(project_path)
    
    # Validate path to prevent traversal
    if not validate_project_path(project_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project path configuration",
        )
    
    # Build code-server URL with folder parameter
    # The workspace path in code-server container is /home/coder/workspace/{project_path}
    workspace_path = f"/home/coder/workspace/{project_path}"
    base_url = get_code_server_base_url()
    
    # URL encode the folder path
    encoded_path = quote(workspace_path, safe="")
    url = f"{base_url}/?folder={encoded_path}"
    
    return CodeServerURLResponse(
        url=url,
        project_name=project.name,
        workspace_path=workspace_path,
    )


@router.get(
    "/url/path/{project_path:path}",
    response_model=CodeServerURLResponse,
    summary="Get code-server URL by path",
    description="""
    Generate a code-server URL for a specific project path.
    
    This endpoint allows direct access by path without project ID.
    Use with caution - validate permissions appropriately.
    """,
    responses={
        400: {"description": "Invalid project path"},
    },
)
async def get_editor_url_by_path(
    project_path: str,
    current_user: CurrentUser,
) -> CodeServerURLResponse:
    """
    Get the code-server URL for a project path directly.
    
    Useful when project path is known but ID is not available.
    """
    # Validate path to prevent traversal
    if not validate_project_path(project_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project path",
        )
    
    # Build code-server URL
    workspace_path = f"/home/coder/workspace/{project_path}"
    base_url = get_code_server_base_url()
    
    encoded_path = quote(workspace_path, safe="")
    url = f"{base_url}/?folder={encoded_path}"
    
    return CodeServerURLResponse(
        url=url,
        project_name=os.path.basename(project_path),
        workspace_path=workspace_path,
    )
