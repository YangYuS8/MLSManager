"""Dataset catalog endpoints."""

import json

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.dataset import Dataset
from app.models.node import Node
from app.schemas.dataset import DatasetCreate, DatasetRead, DatasetUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=list[DatasetRead],
    summary="List all datasets",
    description="Retrieve a paginated list of all datasets, optionally filtered by node.",
)
async def list_datasets(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    node_id: int | None = Query(None, description="Filter by node ID"),
) -> list[Dataset]:
    """
    List all datasets in the catalog.

    - **skip**: Pagination offset
    - **limit**: Maximum number of results
    - **node_id**: Optional filter by node
    """
    query = select(Dataset)
    if node_id is not None:
        query = query.where(Dataset.node_id == node_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new dataset",
    description="Register a new dataset entry in the catalog.",
    responses={
        201: {"description": "Dataset registered successfully"},
        400: {"description": "Node not found"},
    },
)
async def create_dataset(
    db: DbSession,
    current_user: CurrentUser,
    dataset_in: DatasetCreate,
) -> Dataset:
    """
    Register a new dataset in the catalog.

    - **name**: Dataset name
    - **node_id**: ID of the node where dataset is stored
    - **local_path**: Path to dataset on the node
    - **format**: Dataset format (csv, parquet, etc.)
    - **tags**: Optional list of tags for categorization
    """
    # Verify node exists
    result = await db.execute(select(Node).where(Node.id == dataset_in.node_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Node not found",
        )

    tags_json = json.dumps(dataset_in.tags) if dataset_in.tags else None

    dataset = Dataset(
        name=dataset_in.name,
        description=dataset_in.description,
        version=dataset_in.version,
        node_id=dataset_in.node_id,
        local_path=dataset_in.local_path,
        format=dataset_in.format,
        tags=tags_json,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.get(
    "/{dataset_id}",
    response_model=DatasetRead,
    summary="Get dataset by ID",
    description="Retrieve detailed information about a specific dataset.",
    responses={
        200: {"description": "Dataset found"},
        404: {"description": "Dataset not found"},
    },
)
async def get_dataset(
    db: DbSession,
    current_user: CurrentUser,
    dataset_id: int,
) -> Dataset:
    """Get dataset details by ID."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    return dataset


@router.patch(
    "/{dataset_id}",
    response_model=DatasetRead,
    summary="Update dataset",
    description="Update dataset metadata.",
    responses={
        200: {"description": "Dataset updated successfully"},
        404: {"description": "Dataset not found"},
    },
)
async def update_dataset(
    db: DbSession,
    current_user: CurrentUser,
    dataset_id: int,
    dataset_in: DatasetUpdate,
) -> Dataset:
    """Update dataset information. Only provided fields will be updated."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    update_data = dataset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags" and value is not None:
            setattr(dataset, field, json.dumps(value))
        elif field == "status" and value:
            setattr(dataset, field, value.value)
        else:
            setattr(dataset, field, value)

    await db.commit()
    await db.refresh(dataset)
    return dataset


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete dataset",
    description="Remove a dataset from the catalog. **Admin only.**",
    responses={
        204: {"description": "Dataset deleted successfully"},
        404: {"description": "Dataset not found"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def delete_dataset(
    db: DbSession,
    admin_user: AdminUser,
    dataset_id: int,
) -> None:
    """Delete a dataset. Requires admin privileges."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    await db.delete(dataset)
    await db.commit()
