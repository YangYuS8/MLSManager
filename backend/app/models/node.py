"""Node model for master/worker server management."""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.job import Job


class NodeType(str, Enum):
    """Node type enumeration."""

    MASTER = "master"
    WORKER = "worker"


class NodeStatus(str, Enum):
    """Node status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Node(Base):
    """Node model representing a server in the cluster."""

    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    node_type: Mapped[str] = mapped_column(String(20), default=NodeType.WORKER.value)
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=8000)
    status: Mapped[str] = mapped_column(String(20), default=NodeStatus.OFFLINE.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Hardware info (reported by agent)
    cpu_count: Mapped[int | None] = mapped_column(Integer)
    memory_total_gb: Mapped[int | None] = mapped_column(Integer)
    gpu_count: Mapped[int | None] = mapped_column(Integer)
    gpu_info: Mapped[str | None] = mapped_column(Text)  # JSON string

    # Storage info
    storage_path: Mapped[str | None] = mapped_column(String(500))
    storage_total_gb: Mapped[int | None] = mapped_column(Integer)
    storage_used_gb: Mapped[int | None] = mapped_column(Integer)

    # Timestamps
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    datasets: Mapped[list["Dataset"]] = relationship("Dataset", back_populates="node")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="node")

    def __repr__(self) -> str:
        return f"<Node(id={self.id}, node_id={self.node_id}, status={self.status})>"
