"""Project management API endpoints."""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.node import Node
from app.models.project import Project, ProjectStatus
from app.schemas.project import (
    ProjectCloneRequest,
    ProjectCreate,
    ProjectFileContent,
    ProjectFileInfo,
    ProjectFileUpdate,
    ProjectGitStatus,
    ProjectRead,
    ProjectUpdate,
)
from app.services.worker_client import worker_client, WorkerUnreachableError

router = APIRouter()


def get_projects_root() -> str:
    """
    Get the root directory for all projects.
    
    This path is shared with code-server's workspace.
    Uses PROJECTS_ROOT_PATH env var, defaults to ./projects.
    """
    projects_root = os.getenv("PROJECTS_ROOT_PATH", "./projects")
    # Convert to absolute path
    abs_path = os.path.abspath(projects_root)
    # Create directory if it doesn't exist
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def run_git_command(cwd: str, *args: str) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Git command timed out"
    except Exception as e:
        return False, str(e)


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    db: DbSession,
    current_user: CurrentUser,
    node_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Project]:
    """
    List all projects the user has access to.
    
    - Users can see their own projects and public projects
    - Admins can see all projects
    """
    query = select(Project)
    
    # Filter by node if specified
    if node_id is not None:
        query = query.where(Project.node_id == node_id)
    
    # Non-admin users can only see their own or public projects
    if current_user.role == "member":
        query = query.where(
            (Project.owner_id == current_user.id) | (Project.is_public == True)
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    """Create a new project."""
    # Verify node exists
    node_result = await db.execute(
        select(Node).where(Node.id == project_in.node_id)
    )
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    # Determine local path - use provided or auto-generate under PROJECTS_ROOT_PATH
    local_path = project_in.local_path
    if not local_path:
        base_path = get_projects_root()
        local_path = os.path.join(base_path, f"{current_user.id}_{project_in.name}")
    
    # Create project directory if it doesn't exist
    os.makedirs(local_path, exist_ok=True)
    
    # Create project
    project = Project(
        name=project_in.name,
        description=project_in.description,
        git_url=project_in.git_url,
        git_branch=project_in.git_branch,
        local_path=local_path,
        node_id=project_in.node_id,
        owner_id=current_user.id,
        is_public=project_in.is_public,
        auto_sync=project_in.auto_sync,
        status=ProjectStatus.ACTIVE.value,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.post("/clone", response_model=ProjectRead, status_code=status.HTTP_202_ACCEPTED)
async def clone_project(
    clone_request: ProjectCloneRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    """Clone a git repository as a new project (delegated to worker node)."""
    # Verify node exists
    node_result = await db.execute(
        select(Node).where(Node.id == clone_request.node_id)
    )
    node = node_result.scalar_one_or_none()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    # Check if worker node is online
    if not await worker_client.check_node_online(node):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Worker node is offline or unreachable",
        )
    
    # Generate target path (relative path, worker will resolve it)
    if clone_request.local_path:
        target_path = clone_request.local_path
    else:
        # Auto-generate relative path: {user_id}_{project_name}
        target_path = f"{current_user.id}_{clone_request.name}"
    
    # Create project record with PENDING status
    project = Project(
        name=clone_request.name,
        description=clone_request.description,
        git_url=clone_request.git_url,
        git_branch=clone_request.git_branch,
        local_path=target_path,  # Store relative path
        node_id=clone_request.node_id,
        owner_id=current_user.id,
        status=ProjectStatus.PENDING.value,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # Send clone request to worker node
    try:
        accepted = await worker_client.clone_project(
            node=node,
            project_id=project.id,
            git_url=clone_request.git_url,
            branch=clone_request.git_branch,
            target_path=target_path,
        )
        
        if accepted:
            project.status = ProjectStatus.SYNCING.value
        else:
            project.status = ProjectStatus.ERROR.value
            project.sync_error = "Worker rejected clone request"
        
        await db.commit()
        await db.refresh(project)
        
    except WorkerUnreachableError as e:
        project.status = ProjectStatus.ERROR.value
        project.sync_error = str(e)
        await db.commit()
        await db.refresh(project)
    
    return project


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    """Get a project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check access
    if (
        project.owner_id != current_user.id
        and not project.is_public
        and current_user.role == "member"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Project:
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check ownership
    if project.owner_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can update this project",
        )
    
    # Update fields
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "status":
                setattr(project, field, value.value)
            else:
                setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
    delete_files: bool = True,  # Default to True: always delete local files
) -> None:
    """Delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check ownership
    if project.owner_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete this project",
        )
    
    # Optionally delete files on worker node
    if delete_files and project.local_path:
        # Get node to send delete request
        node_result = await db.execute(
            select(Node).where(Node.id == project.node_id)
        )
        node = node_result.scalar_one_or_none()
        
        if node:
            try:
                await worker_client.delete_project(
                    node=node,
                    project_id=project.id,
                    project_path=project.local_path,
                )
            except WorkerUnreachableError:
                # Worker offline, continue with DB deletion
                # Files can be cleaned up manually later
                pass
    
    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/files", response_model=list[ProjectFileInfo])
async def list_project_files(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
    path: str = "",
) -> list[ProjectFileInfo]:
    """List files in a project directory."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check access
    if (
        project.owner_id != current_user.id
        and not project.is_public
        and current_user.role == "member"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Build full path
    full_path = os.path.join(project.local_path, path)
    
    # Security check - prevent path traversal
    full_path = os.path.normpath(full_path)
    if not full_path.startswith(project.local_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path",
        )
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Path not found",
        )
    
    if not os.path.isdir(full_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is not a directory",
        )
    
    files = []
    for entry in os.scandir(full_path):
        # Skip .git directory
        if entry.name == ".git":
            continue
        
        try:
            stat = entry.stat()
            files.append(ProjectFileInfo(
                name=entry.name,
                path=os.path.relpath(entry.path, project.local_path),
                is_dir=entry.is_dir(),
                size=stat.st_size if entry.is_file() else None,
                modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            ))
        except OSError:
            continue
    
    # Sort: directories first, then by name
    files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
    
    return files


@router.get("/{project_id}/files/content", response_model=ProjectFileContent)
async def read_project_file(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
    path: str,
) -> ProjectFileContent:
    """Read a file's content from a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check access
    if (
        project.owner_id != current_user.id
        and not project.is_public
        and current_user.role == "member"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Build full path
    full_path = os.path.join(project.local_path, path)
    
    # Security check - prevent path traversal
    full_path = os.path.normpath(full_path)
    if not full_path.startswith(project.local_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path",
        )
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    if not os.path.isfile(full_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path is not a file",
        )
    
    # Read file content
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        encoding = "utf-8"
    except UnicodeDecodeError:
        # Try latin-1 as fallback
        with open(full_path, "r", encoding="latin-1") as f:
            content = f.read()
        encoding = "latin-1"
    
    stat = os.stat(full_path)
    
    return ProjectFileContent(
        path=path,
        content=content,
        encoding=encoding,
        size=stat.st_size,
    )


@router.put("/{project_id}/files/content")
async def update_project_file(
    project_id: int,
    path: str,
    file_update: ProjectFileUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Update a file's content in a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check ownership for write access
    if project.owner_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can modify files",
        )
    
    # Build full path
    full_path = os.path.join(project.local_path, path)
    
    # Security check - prevent path traversal
    full_path = os.path.normpath(full_path)
    if not full_path.startswith(project.local_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path",
        )
    
    # Create parent directories if needed
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Write file
    with open(full_path, "w", encoding=file_update.encoding) as f:
        f.write(file_update.content)
    
    # Auto-commit if message provided
    if file_update.commit_message and project.git_url:
        run_git_command(project.local_path, "add", path)
        run_git_command(
            project.local_path,
            "commit",
            "-m", file_update.commit_message,
        )
    
    return {"status": "ok", "path": path}


@router.get("/{project_id}/git/status", response_model=ProjectGitStatus)
async def get_project_git_status(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ProjectGitStatus:
    """Get git status of a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check access
    if (
        project.owner_id != current_user.id
        and not project.is_public
        and current_user.role == "member"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    if not os.path.exists(os.path.join(project.local_path, ".git")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not a git repository",
        )
    
    # Get current branch
    success, branch = run_git_command(
        project.local_path, "rev-parse", "--abbrev-ref", "HEAD"
    )
    if not success:
        branch = "unknown"
    
    # Get modified files
    _, modified_output = run_git_command(
        project.local_path, "diff", "--name-only"
    )
    modified_files = [f for f in modified_output.split("\n") if f]
    
    # Get untracked files
    _, untracked_output = run_git_command(
        project.local_path, "ls-files", "--others", "--exclude-standard"
    )
    untracked_files = [f for f in untracked_output.split("\n") if f]
    
    # Check if clean
    is_clean = len(modified_files) == 0 and len(untracked_files) == 0
    
    return ProjectGitStatus(
        current_branch=branch,
        is_clean=is_clean,
        modified_files=modified_files,
        untracked_files=untracked_files,
    )


@router.post("/{project_id}/git/pull")
async def pull_project(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Pull latest changes from remote."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check ownership
    if project.owner_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can pull changes",
        )
    
    if not project.git_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no git remote",
        )
    
    # Pull
    success, output = run_git_command(project.local_path, "pull")
    
    if success:
        project.last_sync_at = datetime.now(timezone.utc)
        project.sync_error = None
        await db.commit()
        return {"status": "ok", "output": output}
    else:
        project.sync_error = output
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Git pull failed: {output}",
        )


@router.post("/{project_id}/git/push")
async def push_project(
    project_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Push changes to remote."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Check ownership
    if project.owner_id != current_user.id and current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can push changes",
        )
    
    if not project.git_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no git remote",
        )
    
    # Push
    success, output = run_git_command(project.local_path, "push")
    
    if success:
        project.last_sync_at = datetime.now(timezone.utc)
        await db.commit()
        return {"status": "ok", "output": output}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Git push failed: {output}",
        )
