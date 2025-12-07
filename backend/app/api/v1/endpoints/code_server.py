"""Code-Server API endpoints for project editing."""

import logging
import os
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.node import Node
from app.models.project import Project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code-server", tags=["code-server"])


class CodeServerURLResponse(BaseModel):
    """Response model for code-server URL."""

    url: str
    project_name: str
    workspace_path: str
    node_name: str | None = None
    node_host: str | None = None


class CodeServerStatusResponse(BaseModel):
    """Response model for code-server status."""

    available: bool
    port: int
    base_url: str


def get_code_server_url_for_node(node: Node | None) -> str:
    """
    Get the code-server URL for a specific node.
    
    If node is None, falls back to local code-server configuration.
    """
    if node:
        # Use node's hostname (for network access) and code-server port
        # hostname is the address used to reach the node (localhost in dev, actual IP/hostname in prod)
        host = node.hostname or node.host
        port = node.code_server_port or 8443
    else:
        # Fallback to local configuration (for backward compatibility)
        host = os.getenv("CODE_SERVER_HOST", "localhost")
        port = int(os.getenv("CODE_SERVER_PORT", "8443"))
    
    return f"http://{host}:{port}"


def get_code_server_base_url() -> str:
    """Get the base URL for local code-server (backward compatibility)."""
    port = os.getenv("CODE_SERVER_PORT", "8443")
    host = os.getenv("CODE_SERVER_HOST", "localhost")
    return f"http://{host}:{port}"


def get_projects_root() -> str:
    """Get the projects root path (absolute path)."""
    projects_root = os.getenv("PROJECTS_ROOT_PATH", "./projects")
    # Always return absolute path
    return os.path.abspath(projects_root)


def validate_project_path(project_path: str) -> bool:
    """
    Validate that the project path is safe and within projects root.
    
    Prevents path traversal attacks.
    Only validates the path string, does not check if path exists.
    """
    # Normalize the path to prevent traversal attacks
    # Remove leading slashes and normalize ../ sequences
    normalized = os.path.normpath(project_path)
    
    # Check for path traversal attempts
    if normalized.startswith("..") or normalized.startswith("/"):
        return False
    
    # Check for suspicious patterns
    if ".." in normalized:
        return False
    
    return True


def get_project_workspace_path(project_local_path: str) -> str:
    """
    Convert a project's local_path to the workspace path inside code-server.
    
    The project's local_path might be:
    1. Absolute path on the node (e.g., /data/projects/myproject)
    2. Relative path (e.g., projects/myproject)
    
    In code-server, all projects are under /home/coder/workspace/
    We use the last component of the path as the project folder name.
    """
    # Extract the basename (last path component)
    # This ensures projects are always in the workspace root
    project_name = os.path.basename(os.path.normpath(project_local_path))
    
    if not project_name:
        # Fallback: use the full path but make it safe
        project_name = project_local_path.replace("/", "_").replace("\\", "_")
    
    return f"/home/coder/workspace/{project_name}"


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
    
    The URL will open code-server on the node where the project is stored.
    Each worker node runs its own code-server instance.
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
    The URL points to the code-server instance on the project's node.
    """
    # Fetch project with node relationship
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.node))
        .where(Project.id == project_id)
    )
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
    
    # Get the workspace path inside code-server container
    workspace_path = get_project_workspace_path(project.local_path)
    logger.info(f"Project {project.id} local_path: {project.local_path} -> workspace_path: {workspace_path}")
    
    # Get node information for code-server URL
    node = project.node
    node_name = node.name if node else None
    node_host = node.host if node else None
    
    # Build code-server URL with folder parameter
    # URL points to code-server on the project's node
    base_url = get_code_server_url_for_node(node)
    
    # URL encode the folder path
    encoded_path = quote(workspace_path, safe="")
    url = f"{base_url}/?folder={encoded_path}"
    
    logger.info(f"Generated code-server URL for project {project.id}: {url} (node: {node_name})")
    
    return CodeServerURLResponse(
        url=url,
        project_name=project.name,
        workspace_path=workspace_path,
        node_name=node_name,
        node_host=node_host,
    )


@router.get(
    "/url/path/{project_path:path}",
    response_model=CodeServerURLResponse,
    summary="Get code-server URL by path",
    description="""
    Generate a code-server URL for a specific project path.
    
    This endpoint allows direct access by path without project ID.
    The path should be a folder name within the workspace.
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
    The project_path should be the folder name (no absolute paths).
    """
    # Validate path to prevent traversal
    if not validate_project_path(project_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project path: path traversal not allowed",
        )
    
    # Build code-server URL
    # Use only the basename to ensure security
    safe_path = os.path.basename(os.path.normpath(project_path))
    workspace_path = f"/home/coder/workspace/{safe_path}"
    base_url = get_code_server_base_url()
    
    encoded_path = quote(workspace_path, safe="")
    url = f"{base_url}/?folder={encoded_path}"
    
    return CodeServerURLResponse(
        url=url,
        project_name=safe_path,
        workspace_path=workspace_path,
    )
