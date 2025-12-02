"""Dataset schemas for API validation."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.dataset import DatasetStatus


class DatasetBase(BaseModel):
    """Base dataset schema."""

    name: str = Field(
        ...,
        max_length=200,
        description="Dataset name",
        examples=["ImageNet-1K"],
    )
    description: str | None = Field(
        None,
        description="Dataset description",
        examples=["ImageNet 2012 classification dataset with 1000 classes"],
    )
    version: str = Field(
        default="1.0.0",
        max_length=50,
        description="Dataset version",
        examples=["1.0.0"],
    )


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset entry."""

    node_id: int = Field(
        ...,
        description="ID of the node where dataset is stored",
        examples=[1],
    )
    local_path: str = Field(
        ...,
        max_length=500,
        description="Path to dataset on the node",
        examples=["/data/datasets/imagenet"],
    )
    format: str | None = Field(
        None,
        max_length=50,
        description="Dataset format (csv, parquet, images, etc.)",
        examples=["images"],
    )
    tags: list[str] | None = Field(
        None,
        description="Tags for categorization",
        examples=[["computer-vision", "classification", "benchmark"]],
    )


class DatasetUpdate(BaseModel):
    """Schema for updating dataset info."""

    name: str | None = Field(None, description="New dataset name")
    description: str | None = Field(None, description="New description")
    version: str | None = Field(None, description="New version")
    status: DatasetStatus | None = Field(None, description="Dataset status")
    size_bytes: int | None = Field(None, description="Dataset size in bytes")
    file_count: int | None = Field(None, description="Number of files")
    format: str | None = Field(None, description="Dataset format")
    tags: list[str] | None = Field(None, description="New tags")


class DatasetRead(DatasetBase):
    """Schema for reading dataset data."""

    id: int = Field(..., description="Unique dataset ID")
    node_id: int = Field(..., description="Node where dataset is stored")
    local_path: str = Field(..., description="Path on node")
    size_bytes: int | None = Field(None, description="Size in bytes")
    file_count: int | None = Field(None, description="Number of files")
    format: str | None = Field(None, description="Dataset format")
    tags: str | None = Field(None, description="Tags (JSON string)")
    status: DatasetStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


# ============================================================================
# Agent/Batch Registration Schemas
# ============================================================================


class DatasetScanItem(BaseModel):
    """Single dataset item from agent scan."""

    name: str = Field(..., description="Dataset name (usually directory name)")
    local_path: str = Field(..., description="Absolute path on node")
    size_bytes: int | None = Field(None, description="Total size in bytes")
    file_count: int | None = Field(None, description="Number of files")
    format: str | None = Field(None, description="Detected format")
    description: str | None = Field(None, description="Auto-generated description")


class DatasetBatchRegister(BaseModel):
    """Batch registration request from agent."""

    datasets: list[DatasetScanItem] = Field(
        ...,
        description="List of scanned datasets to register",
    )


class DatasetBatchResult(BaseModel):
    """Result of batch registration."""

    registered: int = Field(..., description="Number of newly registered datasets")
    updated: int = Field(..., description="Number of updated datasets")
    failed: int = Field(..., description="Number of failed registrations")
    errors: list[str] = Field(default_factory=list, description="Error messages")
