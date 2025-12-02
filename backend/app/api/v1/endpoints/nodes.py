"""Node management endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.node import Node
from app.schemas.node import (
    NodeCreate,
    NodeHeartbeat,
    NodeRead,
    NodeRegister,
    NodeRegisterResponse,
    NodeStats,
    NodeUpdate,
)
from app.services.node_service import NodeService

router = APIRouter()


@router.post(
    "/register",
    response_model=NodeRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register worker node (self-registration)",
    description="Called by worker agent to register itself with the master node.",
    responses={
        201: {"description": "Node registered successfully, returns auth token"},
    },
)
async def register_worker_node(
    db: DbSession,
    node_in: NodeRegister,
) -> NodeRegisterResponse:
    """
    Self-registration endpoint for worker agents.

    This is called by the worker agent on startup to:
    - Register the node with the master
    - Obtain an authentication token for subsequent API calls

    No authentication required for initial registration.
    """
    service = NodeService(db)

    system_info = {
        "cpu_count": node_in.cpu_count,
        "memory_total_gb": node_in.memory_total_gb,
        "gpu_count": node_in.gpu_count,
        "gpu_info": node_in.gpu_info,
        "storage_total_gb": node_in.storage_total_gb,
        "storage_used_gb": node_in.storage_used_gb,
    }
    # Remove None values
    system_info = {k: v for k, v in system_info.items() if v is not None}

    node, token = await service.register_node(
        node_id=node_in.node_id,
        name=node_in.name,
        host=node_in.host,
        port=node_in.port,
        storage_path=node_in.storage_path,
        system_info=system_info if system_info else None,
    )

    return NodeRegisterResponse(
        node=NodeRead.model_validate(node),
        token=token,
        message="Node registered successfully",
    )


@router.get(
    "/stats",
    response_model=NodeStats,
    summary="Get node statistics",
    description="Get aggregated statistics for all nodes.",
)
async def get_node_stats(
    db: DbSession,
    current_user: CurrentUser,
) -> NodeStats:
    """Get aggregated node statistics including resource totals."""
    service = NodeService(db)
    stats = await service.get_node_stats()
    return NodeStats(**stats)


@router.get(
    "/",
    response_model=list[NodeRead],
    summary="List all nodes",
    description="Retrieve a paginated list of all registered compute nodes.",
)
async def list_nodes(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> list[Node]:
    """
    List all registered compute nodes.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    result = await db.execute(select(Node).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=NodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new node",
    description="Register a new compute node in the system. **Admin only.**",
    responses={
        201: {"description": "Node registered successfully"},
        400: {"description": "Node ID already exists"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def register_node(
    db: DbSession,
    admin_user: AdminUser,
    node_in: NodeCreate,
) -> Node:
    """
    Register a new compute node. Requires admin privileges.

    - **node_id**: Unique identifier for the node
    - **name**: Human-readable node name
    - **node_type**: Type of node (master/worker)
    - **host**: Node hostname or IP address
    - **port**: Node API port
    """
    # Check if node_id exists
    result = await db.execute(select(Node).where(Node.node_id == node_in.node_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Node ID already registered",
        )

    node = Node(
        node_id=node_in.node_id,
        name=node_in.name,
        node_type=node_in.node_type.value,
        host=node_in.host,
        port=node_in.port,
        storage_path=node_in.storage_path,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


@router.get(
    "/{node_id}",
    response_model=NodeRead,
    summary="Get node by ID",
    description="Retrieve detailed information about a specific node.",
    responses={
        200: {"description": "Node found"},
        404: {"description": "Node not found"},
    },
)
async def get_node(
    db: DbSession,
    current_user: CurrentUser,
    node_id: str,
) -> Node:
    """Get node details by node_id."""
    result = await db.execute(select(Node).where(Node.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    return node


@router.patch(
    "/{node_id}",
    response_model=NodeRead,
    summary="Update node",
    description="Update node configuration. **Admin only.**",
    responses={
        200: {"description": "Node updated successfully"},
        404: {"description": "Node not found"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def update_node(
    db: DbSession,
    admin_user: AdminUser,
    node_id: str,
    node_in: NodeUpdate,
) -> Node:
    """Update node information. Requires admin privileges."""
    result = await db.execute(select(Node).where(Node.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    update_data = node_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(node, field, value.value)
        else:
            setattr(node, field, value)

    await db.commit()
    await db.refresh(node)
    return node


@router.post(
    "/{node_id}/heartbeat",
    response_model=NodeRead,
    summary="Node heartbeat",
    description="Receive heartbeat from worker node agent. Updates node status and resource metrics.",
    responses={
        200: {"description": "Heartbeat received successfully"},
        404: {"description": "Node not found"},
    },
)
async def node_heartbeat(
    db: DbSession,
    node_id: str,
    heartbeat: NodeHeartbeat,
) -> Node:
    """
    Receive heartbeat from worker node.

    This endpoint is called periodically by the worker agent to report:
    - Node status (online/offline)
    - Resource metrics (CPU, memory, GPU, storage)
    """
    result = await db.execute(select(Node).where(Node.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    # Update node status and info
    node.status = heartbeat.status.value
    node.last_heartbeat = datetime.now(timezone.utc)

    if heartbeat.cpu_count is not None:
        node.cpu_count = heartbeat.cpu_count
    if heartbeat.memory_total_gb is not None:
        node.memory_total_gb = heartbeat.memory_total_gb
    if heartbeat.gpu_count is not None:
        node.gpu_count = heartbeat.gpu_count
    if heartbeat.gpu_info is not None:
        node.gpu_info = heartbeat.gpu_info
    if heartbeat.storage_total_gb is not None:
        node.storage_total_gb = heartbeat.storage_total_gb
    if heartbeat.storage_used_gb is not None:
        node.storage_used_gb = heartbeat.storage_used_gb

    await db.commit()
    await db.refresh(node)
    return node


@router.delete(
    "/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete node",
    description="Remove a node from the system. **Admin only.**",
    responses={
        204: {"description": "Node deleted successfully"},
        404: {"description": "Node not found"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def delete_node(
    db: DbSession,
    admin_user: AdminUser,
    node_id: str,
) -> None:
    """Delete a node. Requires admin privileges."""
    result = await db.execute(select(Node).where(Node.node_id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )

    await db.delete(node)
    await db.commit()
