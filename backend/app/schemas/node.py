"""Node schemas for API validation."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.node import NodeStatus, NodeType


class NodeBase(BaseModel):
    """Base node schema."""

    name: str = Field(
        ...,
        max_length=100,
        description="Human-readable node name",
        examples=["GPU Server 1"],
    )
    host: str = Field(
        ...,
        max_length=255,
        description="Node hostname or IP address",
        examples=["192.168.1.100"],
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Node API port",
        examples=[8000],
    )


class NodeCreate(NodeBase):
    """Schema for registering a new node."""

    node_id: str = Field(
        ...,
        max_length=50,
        description="Unique node identifier",
        examples=["worker-001"],
    )
    node_type: NodeType = Field(
        default=NodeType.WORKER,
        description="Type of node (master/worker)",
    )
    storage_path: str | None = Field(
        None,
        description="Base path for data storage on this node",
        examples=["/data"],
    )


class NodeUpdate(BaseModel):
    """Schema for updating node info."""

    name: str | None = Field(None, description="New node name")
    host: str | None = Field(None, description="New hostname/IP")
    port: int | None = Field(None, description="New port number")
    status: NodeStatus | None = Field(None, description="Node status")
    is_active: bool | None = Field(None, description="Whether node is active")
    storage_path: str | None = Field(None, description="Storage path")


class NodeHeartbeat(BaseModel):
    """Schema for node heartbeat updates."""

    status: NodeStatus = Field(
        default=NodeStatus.ONLINE,
        description="Current node status",
    )
    cpu_count: int | None = Field(
        None,
        description="Number of CPU cores",
        examples=[16],
    )
    memory_total_gb: int | None = Field(
        None,
        description="Total memory in GB",
        examples=[64],
    )
    gpu_count: int | None = Field(
        None,
        description="Number of GPUs",
        examples=[4],
    )
    gpu_info: str | None = Field(
        None,
        description="GPU information (JSON string)",
        examples=["NVIDIA A100 40GB, NVIDIA A100 40GB"],
    )
    storage_total_gb: int | None = Field(
        None,
        description="Total storage in GB",
        examples=[2000],
    )
    storage_used_gb: int | None = Field(
        None,
        description="Used storage in GB",
        examples=[500],
    )


class NodeRead(NodeBase):
    """Schema for reading node data."""

    id: int = Field(..., description="Internal node ID")
    node_id: str = Field(..., description="Unique node identifier")
    node_type: NodeType = Field(..., description="Node type")
    status: NodeStatus = Field(..., description="Current status")
    is_active: bool = Field(..., description="Whether node is active")
    cpu_count: int | None = Field(None, description="CPU core count")
    memory_total_gb: int | None = Field(None, description="Total memory (GB)")
    gpu_count: int | None = Field(None, description="GPU count")
    gpu_info: str | None = Field(None, description="GPU information")
    storage_path: str | None = Field(None, description="Storage base path")
    storage_total_gb: int | None = Field(None, description="Total storage (GB)")
    storage_used_gb: int | None = Field(None, description="Used storage (GB)")
    last_heartbeat: datetime | None = Field(None, description="Last heartbeat timestamp")
    created_at: datetime = Field(..., description="Registration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class NodeRegister(BaseModel):
    """Schema for worker node self-registration."""

    node_id: str = Field(
        ...,
        max_length=50,
        description="Unique node identifier",
        examples=["worker-001"],
    )
    name: str = Field(
        ...,
        max_length=100,
        description="Human-readable node name",
        examples=["GPU Server 1"],
    )
    host: str = Field(
        ...,
        max_length=255,
        description="Node hostname or IP (as seen by master)",
        examples=["192.168.1.100"],
    )
    port: int = Field(
        default=8000,
        description="Node API port",
        examples=[8000],
    )
    storage_path: str | None = Field(
        None,
        description="Base path for data storage",
        examples=["/data"],
    )
    # System info
    cpu_count: int | None = Field(None, description="Number of CPU cores")
    memory_total_gb: int | None = Field(None, description="Total memory in GB")
    gpu_count: int | None = Field(None, description="Number of GPUs")
    gpu_info: str | None = Field(None, description="GPU information")
    storage_total_gb: int | None = Field(None, description="Total storage in GB")
    storage_used_gb: int | None = Field(None, description="Used storage in GB")


class NodeRegisterResponse(BaseModel):
    """Response for node registration."""

    node: NodeRead = Field(..., description="Registered node information")
    token: str = Field(..., description="Agent authentication token")
    message: str = Field(default="Node registered successfully")


class NodeStats(BaseModel):
    """Aggregated node statistics."""

    total_nodes: int = Field(..., description="Total number of nodes")
    online_nodes: int = Field(..., description="Number of online nodes")
    offline_nodes: int = Field(..., description="Number of offline nodes")
    total_cpu: int = Field(..., description="Total CPU cores across all nodes")
    total_memory_gb: int = Field(..., description="Total memory in GB")
    total_gpu: int = Field(..., description="Total GPUs")
    total_storage_gb: int = Field(..., description="Total storage in GB")
    used_storage_gb: int = Field(..., description="Used storage in GB")
