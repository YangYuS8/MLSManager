"""Node service for node management and agent authentication."""

from datetime import UTC, datetime, timedelta

from fastapi import Header
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession
from app.core.config import settings
from app.core.security import create_access_token
from app.models.node import Node, NodeStatus

# ============================================================================
# Agent Token Verification (Dependency)
# ============================================================================


async def verify_agent_token(
    db: DbSession,
    x_agent_token: str | None = Header(None, alias="X-Agent-Token"),
) -> Node | None:
    """
    Verify agent token and return associated node.

    This is a FastAPI dependency that:
    1. Extracts the X-Agent-Token header
    2. Decodes and validates the JWT token
    3. Looks up the node in the database
    4. Returns the node if valid, None otherwise
    """
    if not x_agent_token:
        return None

    try:
        payload = jwt.decode(
            x_agent_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        token_type = payload.get("type")
        if token_type != "agent":
            return None

        node_id = payload.get("node_id")
        if not node_id:
            return None

        # Look up the node
        result = await db.execute(select(Node).where(Node.node_id == node_id))
        node = result.scalar_one_or_none()

        return node

    except JWTError:
        return None


class NodeService:
    """Service for node management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_node(
        self,
        node_id: str,
        name: str,
        host: str,
        port: int = 8000,
        storage_path: str | None = None,
        system_info: dict | None = None,
    ) -> tuple[Node, str]:
        """
        Register a new worker node or update existing one.
        Returns the node and an agent token.
        """
        result = await self.db.execute(select(Node).where(Node.node_id == node_id))
        node = result.scalar_one_or_none()

        if node:
            # Update existing node
            node.name = name
            node.host = host
            node.port = port
            node.status = NodeStatus.ONLINE.value
            node.last_heartbeat = datetime.now(UTC)
            if storage_path:
                node.storage_path = storage_path
            if system_info:
                self._update_system_info(node, system_info)
        else:
            # Create new node
            node = Node(
                node_id=node_id,
                name=name,
                node_type="worker",
                host=host,
                port=port,
                status=NodeStatus.ONLINE.value,
                storage_path=storage_path,
                last_heartbeat=datetime.now(UTC),
            )
            if system_info:
                self._update_system_info(node, system_info)
            self.db.add(node)

        await self.db.commit()
        await self.db.refresh(node)

        # Generate agent token
        token = create_access_token(
            data={"sub": f"agent:{node_id}", "type": "agent", "node_id": node_id},
            expires_delta=timedelta(days=365),  # Long-lived token for agents
        )

        return node, token

    def _update_system_info(self, node: Node, info: dict) -> None:
        """Update node with system information."""
        if "cpu_count" in info:
            node.cpu_count = info["cpu_count"]
        if "memory_total_gb" in info:
            node.memory_total_gb = info["memory_total_gb"]
        if "gpu_count" in info:
            node.gpu_count = info["gpu_count"]
        if "gpu_info" in info:
            node.gpu_info = info["gpu_info"]
        if "storage_total_gb" in info:
            node.storage_total_gb = info["storage_total_gb"]
        if "storage_used_gb" in info:
            node.storage_used_gb = info["storage_used_gb"]

    async def check_offline_nodes(self, timeout_seconds: int = 90) -> list[str]:
        """
        Check and mark nodes as offline if heartbeat timeout exceeded.
        Returns list of node IDs that were marked offline.
        """
        threshold = datetime.now(UTC) - timedelta(seconds=timeout_seconds)

        # Find nodes that are online but haven't sent heartbeat
        result = await self.db.execute(
            select(Node).where(
                Node.status == NodeStatus.ONLINE.value,
                Node.last_heartbeat < threshold,
            )
        )
        offline_nodes = result.scalars().all()

        offline_ids = []
        for node in offline_nodes:
            node.status = NodeStatus.OFFLINE.value
            offline_ids.append(node.node_id)

        if offline_ids:
            await self.db.commit()

        return offline_ids

    async def get_node_stats(self) -> dict:
        """Get aggregated statistics for all nodes."""
        result = await self.db.execute(select(Node).where(Node.is_active.is_(True)))
        nodes = result.scalars().all()

        stats = {
            "total_nodes": len(nodes),
            "online_nodes": 0,
            "offline_nodes": 0,
            "total_cpu": 0,
            "total_memory_gb": 0,
            "total_gpu": 0,
            "total_storage_gb": 0,
            "used_storage_gb": 0,
        }

        for node in nodes:
            if node.status == NodeStatus.ONLINE.value:
                stats["online_nodes"] += 1
            else:
                stats["offline_nodes"] += 1

            if node.cpu_count:
                stats["total_cpu"] += node.cpu_count
            if node.memory_total_gb:
                stats["total_memory_gb"] += node.memory_total_gb
            if node.gpu_count:
                stats["total_gpu"] += node.gpu_count
            if node.storage_total_gb:
                stats["total_storage_gb"] += node.storage_total_gb
            if node.storage_used_gb:
                stats["used_storage_gb"] += node.storage_used_gb

        return stats
