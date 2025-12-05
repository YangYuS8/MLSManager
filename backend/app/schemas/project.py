"""Pydantic schemas for project management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    SYNCING = "syncing"
    ERROR = "error"


class ProjectBase(BaseModel):
    """Base schema for project."""

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str | None = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    git_url: str | None = Field(None, description="Git repository URL")
    git_branch: str = Field(default="main", description="Git branch to clone")
    local_path: str = Field(..., description="Local path for the project")
    node_id: int = Field(..., description="Node ID where project resides")
    is_public: bool = Field(default=False, description="Is project publicly visible")
    auto_sync: bool = Field(default=False, description="Auto-sync with git remote")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    git_branch: str | None = None
    is_public: bool | None = None
    auto_sync: bool | None = None
    status: ProjectStatus | None = None


class ProjectRead(ProjectBase):
    """Schema for reading a project."""

    id: int
    git_url: str | None
    git_branch: str
    local_path: str
    status: ProjectStatus
    last_sync_at: datetime | None
    sync_error: str | None
    node_id: int
    owner_id: int
    is_public: bool
    auto_sync: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectFileInfo(BaseModel):
    """Schema for project file info."""

    name: str
    path: str
    is_dir: bool
    size: int | None = None
    modified: datetime | None = None


class ProjectFileContent(BaseModel):
    """Schema for project file content."""

    path: str
    content: str
    encoding: str = "utf-8"
    size: int


class ProjectFileUpdate(BaseModel):
    """Schema for updating a project file."""

    content: str = Field(..., description="New file content")
    encoding: str = Field(default="utf-8", description="File encoding")
    commit_message: str | None = Field(None, description="Git commit message if auto-commit")


class ProjectGitStatus(BaseModel):
    """Schema for project git status."""

    current_branch: str
    is_clean: bool
    modified_files: list[str]
    untracked_files: list[str]
    ahead: int = 0
    behind: int = 0


class ProjectCloneRequest(BaseModel):
    """Schema for cloning a git repository."""

    git_url: str = Field(..., description="Git repository URL to clone")
    git_branch: str = Field(default="main", description="Branch to clone")
    name: str = Field(..., description="Project name")
    description: str | None = None
    node_id: int = Field(..., description="Node to clone to")
    local_path: str | None = Field(None, description="Override local path (auto-generated if not provided)")
