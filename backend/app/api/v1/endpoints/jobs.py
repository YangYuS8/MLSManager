"""Job management endpoints."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.config import settings
from app.models.job import Job, JobStatus
from app.models.node import Node
from app.schemas.job import (
    JobCreate,
    JobLogRead,
    JobLogUpload,
    JobRead,
    JobStats,
    JobStatusUpdate,
    JobUpdate,
)
from app.services.job_service import JobService
from app.services.node_service import verify_agent_token

router = APIRouter()


# ============================================================================
# Agent token dependency
# ============================================================================


async def require_agent_token(
    node: Node | None = Depends(verify_agent_token),
) -> Node:
    """Verify agent token and return node. Raises 401 if invalid."""
    if not node:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing agent token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return node


AgentNode = Depends(require_agent_token)


# ============================================================================
# Log file helpers
# ============================================================================


def get_job_log_path(job_id: int) -> Path:
    """Get the path for job logs storage."""
    log_dir = Path(settings.data_dir) / "logs" / "jobs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"job_{job_id}.log"


@router.get(
    "/stats",
    response_model=JobStats,
    summary="Get job statistics",
    description="Get aggregated job statistics.",
)
async def get_job_stats(
    db: DbSession,
    current_user: CurrentUser,
) -> JobStats:
    """Get aggregated job statistics."""
    service = JobService(db)
    stats = await service.get_job_stats()
    return JobStats(**stats)


@router.get(
    "/queue/{node_id}",
    response_model=list[JobRead],
    summary="Get queued jobs for node",
    description="Get jobs queued for execution on a specific node. Used by worker agents.",
)
async def get_job_queue(
    db: DbSession,
    node_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum jobs to return"),
) -> list[Job]:
    """
    Get queued jobs for a worker node.

    Worker agents call this endpoint to fetch jobs to execute.
    Jobs are returned in FIFO order.
    """
    service = JobService(db)
    jobs = await service.get_pending_jobs_for_node(node_id, limit)
    return jobs


@router.post(
    "/{job_id}/status",
    response_model=JobRead,
    summary="Update job status",
    description="Update job status and execution info. Used by worker agents.",
)
async def update_job_status(
    db: DbSession,
    job_id: int,
    status_update: JobStatusUpdate,
) -> Job:
    """
    Update job status from worker agent.

    Worker agents call this to report:
    - Job started (RUNNING)
    - Job completed (COMPLETED with exit_code=0)
    - Job failed (FAILED with error_message)
    """
    service = JobService(db)
    job = await service.update_job_status(
        job_id=job_id,
        status=status_update.status,
        exit_code=status_update.exit_code,
        error_message=status_update.error_message,
        log_path=status_update.log_path,
        output_path=status_update.output_path,
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.post(
    "/auto-assign",
    response_model=dict,
    summary="Auto-assign pending jobs",
    description="Automatically assign all pending jobs to available nodes. **Admin only.**",
)
async def auto_assign_jobs(
    db: DbSession,
    admin_user: AdminUser,
) -> dict:
    """Trigger automatic job assignment for all pending jobs."""
    service = JobService(db)
    count = await service.auto_assign_pending_jobs()
    return {"assigned_jobs": count, "message": f"Assigned {count} jobs to nodes"}


@router.get(
    "/",
    response_model=list[JobRead],
    summary="List all jobs",
    description="Retrieve a paginated list of jobs with optional filtering.",
)
async def list_jobs(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    status_filter: JobStatus | None = Query(None, description="Filter by job status"),
    node_id: int | None = Query(None, description="Filter by node ID"),
) -> list[Job]:
    """
    List all jobs with optional filtering.

    - **skip**: Pagination offset
    - **limit**: Maximum number of results
    - **status_filter**: Filter by job status (pending/running/completed/failed/cancelled)
    - **node_id**: Filter by assigned node
    """
    query = select(Job)
    if status_filter:
        query = query.where(Job.status == status_filter.value)
    if node_id is not None:
        query = query.where(Job.node_id == node_id)
    query = query.offset(skip).limit(limit).order_by(Job.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit new job",
    description="Submit a new ML training or processing job.",
    responses={
        201: {"description": "Job submitted successfully"},
        400: {"description": "Invalid node ID"},
    },
)
async def create_job(
    db: DbSession,
    current_user: CurrentUser,
    job_in: JobCreate,
) -> Job:
    """
    Submit a new job for execution.

    - **name**: Job name for identification
    - **command**: Command to execute
    - **job_type**: Execution environment (docker/conda/venv)
    - **image**: Docker image (for docker jobs)
    - **node_id**: Target node (optional, auto-assigned if not specified)
    - **cpu_limit**: CPU core limit
    - **memory_limit_gb**: Memory limit in GB
    - **gpu_count**: Number of GPUs required
    """
    # Verify node if specified
    if job_in.node_id:
        result = await db.execute(select(Node).where(Node.id == job_in.node_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node not found",
            )

    env_json = json.dumps(job_in.environment) if job_in.environment else None

    job = Job(
        name=job_in.name,
        description=job_in.description,
        owner_id=current_user.id,
        node_id=job_in.node_id,
        job_type=job_in.job_type.value,
        image=job_in.image,
        command=job_in.command,
        working_dir=job_in.working_dir,
        environment=env_json,
        cpu_limit=job_in.cpu_limit,
        memory_limit_gb=job_in.memory_limit_gb,
        gpu_count=job_in.gpu_count,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get(
    "/{job_id}",
    response_model=JobRead,
    summary="Get job by ID",
    description="Retrieve detailed information about a specific job.",
    responses={
        200: {"description": "Job found"},
        404: {"description": "Job not found"},
    },
)
async def get_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: int,
) -> Job:
    """Get job details including status, logs, and output information."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.patch(
    "/{job_id}",
    response_model=JobRead,
    summary="Update job",
    description="Update job information. Owner or admin only.",
    responses={
        200: {"description": "Job updated successfully"},
        404: {"description": "Job not found"},
        403: {"description": "Not authorized to modify this job"},
    },
)
async def update_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: int,
    job_in: JobUpdate,
) -> Job:
    """Update job information. Only the job owner or admin can update."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership or admin
    if job.owner_id != current_user.id and current_user.role == "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this job",
        )

    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(job, field, value.value)
        else:
            setattr(job, field, value)

    await db.commit()
    await db.refresh(job)
    return job


@router.post(
    "/{job_id}/cancel",
    response_model=JobRead,
    summary="Cancel job",
    description="Cancel a running or pending job. Owner or admin only.",
    responses={
        200: {"description": "Job cancelled successfully"},
        400: {"description": "Job cannot be cancelled (already completed/failed/cancelled)"},
        404: {"description": "Job not found"},
        403: {"description": "Not authorized to cancel this job"},
    },
)
async def cancel_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: int,
) -> Job:
    """Cancel a job. Only pending or running jobs can be cancelled."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership or admin
    if job.owner_id != current_user.id and current_user.role == "member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to cancel this job",
        )

    if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in {job.status} status",
        )

    job.status = JobStatus.CANCELLED.value
    await db.commit()
    await db.refresh(job)
    return job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job",
    description="Delete a job record. **Admin only.**",
    responses={
        204: {"description": "Job deleted successfully"},
        404: {"description": "Job not found"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def delete_job(
    db: DbSession,
    admin_user: AdminUser,
    job_id: int,
) -> None:
    """Delete a job record. Requires admin privileges."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    await db.delete(job)
    await db.commit()


# ============================================================================
# Job Logs Endpoints
# ============================================================================


@router.post(
    "/{job_id}/logs",
    response_model=dict,
    summary="Upload job logs",
    description="Worker agent uploads job execution logs.",
    responses={
        200: {"description": "Logs uploaded successfully"},
        401: {"description": "Invalid agent token"},
        404: {"description": "Job not found"},
    },
)
async def upload_job_logs(
    db: DbSession,
    job_id: int,
    log_data: JobLogUpload,
    node: Node = AgentNode,
) -> dict:
    """
    Upload job execution logs from worker agent.

    Requires valid agent token in X-Agent-Token header.
    """
    # Verify job exists and belongs to this node
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.node_id != node.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job is not assigned to this node",
        )

    # Write logs to file
    log_path = get_job_log_path(job_id)
    mode = "a" if log_data.append else "w"

    with open(log_path, mode, encoding="utf-8") as f:
        f.write(log_data.content)

    # Update job log_path
    job.log_path = str(log_path)
    await db.commit()

    return {
        "message": "Logs uploaded successfully",
        "log_path": str(log_path),
        "size_bytes": log_path.stat().st_size,
    }


@router.get(
    "/{job_id}/logs",
    response_class=PlainTextResponse,
    summary="Get job logs",
    description="Retrieve job execution logs.",
    responses={
        200: {"description": "Log content returned"},
        404: {"description": "Job or logs not found"},
    },
)
async def get_job_logs(
    db: DbSession,
    current_user: CurrentUser,
    job_id: int,
    tail: int | None = Query(None, description="Return only last N lines"),
) -> str:
    """
    Get job execution logs.

    - **tail**: Optional, return only last N lines of the log
    """
    # Verify job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    log_path = get_job_log_path(job_id)
    if not log_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No logs available for this job",
        )

    content = log_path.read_text(encoding="utf-8")

    if tail and tail > 0:
        lines = content.splitlines()
        content = "\n".join(lines[-tail:])

    return content


@router.get(
    "/{job_id}/logs/info",
    response_model=JobLogRead,
    summary="Get job logs info",
    description="Get metadata about job logs without fetching content.",
)
async def get_job_logs_info(
    db: DbSession,
    current_user: CurrentUser,
    job_id: int,
) -> JobLogRead:
    """Get job logs metadata."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    log_path = get_job_log_path(job_id)
    if not log_path.exists():
        return JobLogRead(
            job_id=job_id,
            content="",
            size_bytes=0,
            last_updated=None,
        )

    stat = log_path.stat()
    from datetime import UTC, datetime

    return JobLogRead(
        job_id=job_id,
        content="[Use GET /jobs/{job_id}/logs to fetch content]",
        size_bytes=stat.st_size,
        last_updated=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
    )
