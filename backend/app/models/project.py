"""Project model for code project management."""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.node import Node
    from app.models.user import User


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    SYNCING = "syncing"
    ERROR = "error"


class Project(Base):
    """Project model for managing code repositories."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Git repository info
    git_url: Mapped[str | None] = mapped_column(String(500))  # Remote URL
    git_branch: Mapped[str] = mapped_column(String(100), default="main")
    local_path: Mapped[str] = mapped_column(String(500))  # Local clone path
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default=ProjectStatus.ACTIVE.value)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_error: Mapped[str | None] = mapped_column(Text)
    
    # Relations
    node_id: Mapped[int] = mapped_column(Integer, ForeignKey("nodes.id"))
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_sync: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    node: Mapped["Node"] = relationship("Node", back_populates="projects")
    owner: Mapped["User"] = relationship("User", back_populates="projects")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"
