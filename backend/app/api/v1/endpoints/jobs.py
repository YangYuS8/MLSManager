"""Job management endpoints."""

import json

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.job import Job, JobStatus
from app.models.node import Node
from app.schemas.job import JobCreate, JobRead, JobUpdate

router = APIRouter()


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
