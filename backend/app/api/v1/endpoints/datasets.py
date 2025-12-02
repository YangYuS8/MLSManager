"""Dataset catalog endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.dataset import Dataset, DatasetStatus
from app.models.node import Node
from app.schemas.dataset import (
    DatasetBatchRegister,
    DatasetBatchResult,
    DatasetCreate,
    DatasetRead,
    DatasetUpdate,
)
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


# ============================================================================
# Agent Endpoints (Worker node)
# ============================================================================


@router.post(
    "/batch",
    response_model=DatasetBatchResult,
    summary="Batch register datasets from agent",
    description="Worker agent reports scanned datasets. Creates new or updates existing.",
    responses={
        200: {"description": "Batch registration completed"},
        401: {"description": "Invalid agent token"},
    },
)
async def batch_register_datasets(
    db: DbSession,
    batch_in: DatasetBatchRegister,
    node: Node = AgentNode,
) -> DatasetBatchResult:
    """
    Batch register or update datasets from worker agent scan.

    This endpoint is called by worker agents after scanning their local
    dataset directories. It will:
    - Create new dataset entries for paths not yet registered
    - Update existing entries if path already registered for this node
    - Mark datasets as READY status

    Requires valid agent token in X-Agent-Token header.
    """
    registered = 0
    updated = 0
    failed = 0
    errors: list[str] = []

    for item in batch_in.datasets:
        try:
            # Check if dataset already exists for this node + path
            result = await db.execute(
                select(Dataset).where(
                    Dataset.node_id == node.id,
                    Dataset.local_path == item.local_path,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing dataset
                existing.name = item.name
                existing.size_bytes = item.size_bytes
                existing.file_count = item.file_count
                existing.format = item.format
                existing.status = DatasetStatus.AVAILABLE
                if item.description:
                    existing.description = item.description
                updated += 1
            else:
                # Create new dataset
                dataset = Dataset(
                    name=item.name,
                    description=item.description,
                    node_id=node.id,
                    local_path=item.local_path,
                    size_bytes=item.size_bytes,
                    file_count=item.file_count,
                    format=item.format,
                    status=DatasetStatus.AVAILABLE,
                )
                db.add(dataset)
                registered += 1

        except Exception as e:
            failed += 1
            errors.append(f"Failed to register {item.local_path}: {e!s}")

    await db.commit()

    return DatasetBatchResult(
        registered=registered,
        updated=updated,
        failed=failed,
        errors=errors,
    )


@router.get(
    "/node/{node_id}",
    response_model=list[DatasetRead],
    summary="Get datasets by node",
    description="List all datasets on a specific node.",
)
async def list_node_datasets(
    db: DbSession,
    current_user: CurrentUser,
    node_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[Dataset]:
    """List all datasets registered on a specific node."""
    query = (
        select(Dataset)
        .where(Dataset.node_id == node_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/search",
    response_model=list[DatasetRead],
    summary="Search datasets",
    description="Search datasets by name, format, or tags.",
)
async def search_datasets(
    db: DbSession,
    current_user: CurrentUser,
    q: str = Query(..., min_length=1, description="Search query"),
    format: str | None = Query(None, description="Filter by format"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[Dataset]:
    """
    Search datasets by name or description.

    - **q**: Search query (matches name or description)
    - **format**: Optional format filter
    """
    query = select(Dataset).where(
        (Dataset.name.ilike(f"%{q}%")) | (Dataset.description.ilike(f"%{q}%"))
    )

    if format:
        query = query.where(Dataset.format == format)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
