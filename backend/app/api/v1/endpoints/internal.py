"""Internal API endpoints for worker node callbacks."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.node import Node
from app.models.project import Project, ProjectStatus

router = APIRouter()


class ProjectStatusUpdate(BaseModel):
    """Request body for project status update."""
    status: str
    message: Optional[str] = None
    local_path: Optional[str] = None


@router.post("/projects/{project_id}/status")
async def update_project_status(
    project_id: int,
    update: ProjectStatusUpdate,
    db: DbSession,
    x_agent_token: str = Header(..., description="Worker agent authentication token"),
) -> dict:
    """
    Worker callback endpoint to update project status.
    
    Called by worker nodes after completing file operations like clone/pull.
    """
    # Get the project
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Verify the token matches the project's node
    node_result = await db.execute(
        select(Node).where(Node.id == project.node_id)
    )
    node = node_result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    # Validate agent token
    if not node.agent_token or node.agent_token != x_agent_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent token",
        )
    
    # Update project status
    valid_statuses = {s.value for s in ProjectStatus}
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {update.status}",
        )
    
    project.status = update.status
    
    if update.message:
        if update.status == ProjectStatus.ERROR.value:
            project.sync_error = update.message
        else:
            # Clear error on success
            project.sync_error = None
    
    if update.local_path:
        project.local_path = update.local_path
    
    if update.status == ProjectStatus.ACTIVE.value:
        project.last_sync_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {
        "success": True,
        "project_id": project_id,
        "status": project.status,
    }


class JobStatusUpdate(BaseModel):
    """Request body for job status update."""
    status: str
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    output: Optional[str] = None


@router.post("/jobs/{job_id}/status")
async def update_job_status(
    job_id: int,
    update: JobStatusUpdate,
    db: DbSession,
    x_agent_token: str = Header(..., description="Worker agent authentication token"),
) -> dict:
    """
    Worker callback endpoint to update job status.
    
    Called by worker nodes after job execution completes.
    """
    from app.models.job import Job
    
    # Get the job
    job_result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    # Verify the token matches the job's node
    node_result = await db.execute(
        select(Node).where(Node.id == job.node_id)
    )
    node = node_result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    # Validate agent token
    if not node.agent_token or node.agent_token != x_agent_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent token",
        )
    
    # Update job status
    job.status = update.status
    
    if update.exit_code is not None:
        job.exit_code = update.exit_code
    
    if update.error_message:
        job.error_message = update.error_message
    
    if update.status in ("completed", "failed", "cancelled"):
        job.finished_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {
        "success": True,
        "job_id": job_id,
        "status": job.status,
    }
