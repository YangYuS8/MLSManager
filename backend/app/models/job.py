"""Job model for ML training/inference task management."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.node import Node
from app.models.user import User


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job execution environment type."""

    DOCKER = "docker"
    CONDA = "conda"
    VENV = "venv"


class Job(Base):
    """Job model for ML task execution."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Ownership
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Execution target
    node_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"))

    # Job configuration
    job_type: Mapped[str] = mapped_column(String(20), default=JobType.DOCKER.value)
    image: Mapped[str | None] = mapped_column(String(500))  # Docker image or env name
    command: Mapped[str] = mapped_column(Text)
    working_dir: Mapped[str | None] = mapped_column(String(500))
    environment: Mapped[str | None] = mapped_column(Text)  # JSON dict of env vars

    # Resource requirements
    cpu_limit: Mapped[int | None] = mapped_column(Integer)
    memory_limit_gb: Mapped[int | None] = mapped_column(Integer)
    gpu_count: Mapped[int | None] = mapped_column(Integer)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING.value)
    exit_code: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Output
    output_path: Mapped[str | None] = mapped_column(String(500))
    log_path: Mapped[str | None] = mapped_column(String(500))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="jobs")
    node: Mapped["Node | None"] = relationship("Node", back_populates="jobs")

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, name={self.name}, status={self.status})>"
