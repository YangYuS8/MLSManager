"""Job schemas for API validation."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.job import JobStatus, JobType


class JobBase(BaseModel):
    """Base job schema."""

    name: str = Field(
        ...,
        max_length=200,
        description="Job name for identification",
        examples=["Train ResNet50 on ImageNet"],
    )
    description: str | None = Field(
        None,
        description="Job description",
        examples=["Fine-tune ResNet50 model on ImageNet dataset"],
    )


class JobCreate(JobBase):
    """Schema for creating a new job."""

    job_type: JobType = Field(
        default=JobType.DOCKER,
        description="Execution environment type",
    )
    image: str | None = Field(
        None,
        max_length=500,
        description="Docker image (for docker jobs)",
        examples=["pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime"],
    )
    command: str = Field(
        ...,
        description="Command to execute",
        examples=["python train.py --epochs 100 --batch-size 32"],
    )
    working_dir: str | None = Field(
        None,
        description="Working directory for the command",
        examples=["/workspace"],
    )
    environment: dict[str, str] | None = Field(
        None,
        description="Environment variables",
        examples=[{"CUDA_VISIBLE_DEVICES": "0,1", "WANDB_PROJECT": "imagenet"}],
    )
    node_id: int | None = Field(
        None,
        description="Target node ID (auto-assigned if not specified)",
    )
    cpu_limit: int | None = Field(
        None,
        description="CPU core limit",
        examples=[8],
    )
    memory_limit_gb: int | None = Field(
        None,
        description="Memory limit in GB",
        examples=[32],
    )
    gpu_count: int | None = Field(
        None,
        description="Number of GPUs required",
        examples=[2],
    )


class JobUpdate(BaseModel):
    """Schema for updating job info."""

    name: str | None = Field(None, description="New job name")
    description: str | None = Field(None, description="New description")
    status: JobStatus | None = Field(None, description="New job status")
    node_id: int | None = Field(None, description="Assign to different node")


class JobRead(JobBase):
    """Schema for reading job data."""

    id: int = Field(..., description="Unique job ID")
    owner_id: int = Field(..., description="ID of user who created the job")
    node_id: int | None = Field(None, description="Assigned node ID")
    job_type: JobType = Field(..., description="Execution environment type")
    image: str | None = Field(None, description="Docker image")
    command: str = Field(..., description="Execution command")
    working_dir: str | None = Field(None, description="Working directory")
    environment: str | None = Field(None, description="Environment variables (JSON)")
    cpu_limit: int | None = Field(None, description="CPU limit")
    memory_limit_gb: int | None = Field(None, description="Memory limit (GB)")
    gpu_count: int | None = Field(None, description="GPU count")
    status: JobStatus = Field(..., description="Current job status")
    exit_code: int | None = Field(None, description="Process exit code")
    error_message: str | None = Field(None, description="Error message if failed")
    output_path: str | None = Field(None, description="Path to job outputs")
    log_path: str | None = Field(None, description="Path to job logs")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(None, description="Job start timestamp")
    completed_at: datetime | None = Field(None, description="Job completion timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class JobStatusUpdate(BaseModel):
    """Schema for worker agent to update job status."""

    status: JobStatus = Field(..., description="New job status")
    exit_code: int | None = Field(None, description="Process exit code (for completed/failed)")
    error_message: str | None = Field(None, description="Error message if failed")
    log_path: str | None = Field(None, description="Path to job logs on node")
    output_path: str | None = Field(None, description="Path to job outputs on node")


class JobStats(BaseModel):
    """Aggregated job statistics."""

    total_jobs: int = Field(..., description="Total number of jobs")
    pending_jobs: int = Field(..., description="Jobs waiting for assignment")
    queued_jobs: int = Field(..., description="Jobs assigned but not started")
    running_jobs: int = Field(..., description="Currently running jobs")
    completed_jobs: int = Field(..., description="Successfully completed jobs")
    failed_jobs: int = Field(..., description="Failed jobs")
    cancelled_jobs: int = Field(..., description="Cancelled jobs")


class JobLogUpload(BaseModel):
    """Schema for uploading job logs from worker agent."""

    content: str = Field(..., description="Log content (text)")
    append: bool = Field(
        default=True,
        description="Append to existing log (True) or overwrite (False)",
    )


class JobLogRead(BaseModel):
    """Schema for reading job logs."""

    job_id: int = Field(..., description="Job ID")
    content: str = Field(..., description="Log content")
    size_bytes: int = Field(..., description="Log size in bytes")
    last_updated: datetime | None = Field(None, description="Last update time")
