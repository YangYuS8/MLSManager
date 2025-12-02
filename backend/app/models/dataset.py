"""Dataset model for managing ML datasets across nodes."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.node import Node


class DatasetStatus(str, Enum):
    """Dataset status enumeration."""

    PENDING = "pending"
    AVAILABLE = "available"
    SYNCING = "syncing"
    ERROR = "error"


class Dataset(Base):
    """Dataset model for ML data catalog."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")

    # Location
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    local_path: Mapped[str] = mapped_column(String(500))

    # Metadata
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    file_count: Mapped[int | None] = mapped_column(Integer)
    format: Mapped[str | None] = mapped_column(String(50))  # e.g., "images", "csv", "parquet"
    tags: Mapped[str | None] = mapped_column(Text)  # JSON array of tags

    # Status
    status: Mapped[str] = mapped_column(String(20), default=DatasetStatus.PENDING.value)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    node: Mapped["Node"] = relationship("Node", back_populates="datasets")

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, status={self.status})>"
