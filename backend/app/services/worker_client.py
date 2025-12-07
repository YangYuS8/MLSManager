"""Worker client service for communicating with worker nodes."""

import httpx
from typing import Optional

from app.models.node import Node


class WorkerUnreachableError(Exception):
    """Worker node is not reachable."""
    pass


class WorkerClient:
    """HTTP client for communicating with worker nodes."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def check_node_online(self, node: Node) -> bool:
        """Check if a worker node is reachable.
        
        Args:
            node: The node to check.
            
        Returns:
            True if the node is online, False otherwise.
        """
        if not node.hostname or not node.agent_port:
            return False
            
        url = f"http://{node.hostname}:{node.agent_port}/health"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url)
                return response.status_code == 200
            except httpx.RequestError:
                return False

    async def clone_project(
        self,
        node: Node,
        project_id: int,
        git_url: str,
        branch: str,
        target_path: str,
    ) -> bool:
        """Send a clone request to a worker node.
        
        Args:
            node: The target worker node.
            project_id: The project database ID.
            git_url: The Git repository URL to clone.
            branch: The branch to clone.
            target_path: The relative path for the cloned project.
            
        Returns:
            True if the request was accepted.
            
        Raises:
            WorkerUnreachableError: If the worker cannot be reached.
        """
        if not node.hostname or not node.agent_port:
            raise WorkerUnreachableError("Node missing hostname or agent_port")
            
        url = f"http://{node.hostname}:{node.agent_port}/api/v1/projects/clone"
        headers = {"X-Agent-Token": node.agent_token or ""}
        payload = {
            "project_id": project_id,
            "git_url": git_url,
            "branch": branch,
            "target_path": target_path,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                return response.status_code == 202  # Accepted
            except httpx.RequestError as e:
                raise WorkerUnreachableError(f"Cannot reach worker: {e}")

    async def pull_project(
        self,
        node: Node,
        project_id: int,
        project_path: str,
        branch: Optional[str] = None,
    ) -> dict:
        """Send a pull request to a worker node.
        
        Args:
            node: The target worker node.
            project_id: The project database ID.
            project_path: The relative path of the project.
            branch: The branch to pull (optional).
            
        Returns:
            The pull result from the worker.
            
        Raises:
            WorkerUnreachableError: If the worker cannot be reached.
        """
        if not node.hostname or not node.agent_port:
            raise WorkerUnreachableError("Node missing hostname or agent_port")
            
        url = f"http://{node.hostname}:{node.agent_port}/api/v1/projects/{project_id}/pull"
        headers = {"X-Agent-Token": node.agent_token or ""}
        payload = {
            "project_path": project_path,
            "branch": branch or "",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                return response.json()
            except httpx.RequestError as e:
                raise WorkerUnreachableError(f"Cannot reach worker: {e}")

    async def get_project_status(
        self,
        node: Node,
        project_id: int,
        project_path: str,
    ) -> dict:
        """Get project status from a worker node.
        
        Args:
            node: The target worker node.
            project_id: The project database ID.
            project_path: The relative path of the project.
            
        Returns:
            The project/git status from the worker.
            
        Raises:
            WorkerUnreachableError: If the worker cannot be reached.
        """
        if not node.hostname or not node.agent_port:
            raise WorkerUnreachableError("Node missing hostname or agent_port")
            
        url = f"http://{node.hostname}:{node.agent_port}/api/v1/projects/{project_id}/status"
        headers = {"X-Agent-Token": node.agent_token or ""}
        params = {"project_path": project_path}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                return response.json()
            except httpx.RequestError as e:
                raise WorkerUnreachableError(f"Cannot reach worker: {e}")

    async def delete_project(
        self,
        node: Node,
        project_id: int,
        project_path: str,
    ) -> bool:
        """Delete a project from a worker node.
        
        Args:
            node: The target worker node.
            project_id: The project database ID.
            project_path: The relative path of the project.
            
        Returns:
            True if deletion was successful.
            
        Raises:
            WorkerUnreachableError: If the worker cannot be reached.
        """
        if not node.hostname or not node.agent_port:
            raise WorkerUnreachableError("Node missing hostname or agent_port")
            
        url = f"http://{node.hostname}:{node.agent_port}/api/v1/projects/{project_id}"
        headers = {"X-Agent-Token": node.agent_token or ""}
        payload = {"project_path": project_path}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    "DELETE", url, json=payload, headers=headers
                )
                return response.status_code == 200
            except httpx.RequestError as e:
                raise WorkerUnreachableError(f"Cannot reach worker: {e}")


# Global singleton instance
worker_client = WorkerClient()
