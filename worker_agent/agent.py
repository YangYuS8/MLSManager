"""Worker Agent for ML-Server-Manager.

This agent runs on worker nodes and communicates with the master node to:
- Report node status and resource usage
- Send heartbeats
- Execute jobs (Docker/conda/venv)
- Scan and report local datasets
"""

import asyncio
import platform
import os
from datetime import datetime

import httpx
from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    """Agent configuration settings."""

    master_url: str = "http://localhost:8000"
    node_id: str = "worker-001"
    heartbeat_interval: int = 30  # seconds
    storage_path: str = "/data"

    class Config:
        env_prefix = "AGENT_"


settings = AgentSettings()


def get_system_info() -> dict:
    """Collect system information."""
    import shutil

    info = {
        "cpu_count": os.cpu_count(),
        "memory_total_gb": None,
        "gpu_count": 0,
        "gpu_info": None,
        "storage_total_gb": None,
        "storage_used_gb": None,
    }

    # Try to get memory info
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb = int(line.split()[1])
                    info["memory_total_gb"] = mem_kb // (1024 * 1024)
                    break
    except Exception:
        pass

    # Try to get GPU info (nvidia-smi)
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            gpus = result.stdout.strip().split("\n")
            info["gpu_count"] = len(gpus)
            info["gpu_info"] = result.stdout.strip()
    except Exception:
        pass

    # Get storage info
    try:
        if os.path.exists(settings.storage_path):
            usage = shutil.disk_usage(settings.storage_path)
            info["storage_total_gb"] = usage.total // (1024**3)
            info["storage_used_gb"] = usage.used // (1024**3)
    except Exception:
        pass

    return info


async def send_heartbeat(client: httpx.AsyncClient) -> bool:
    """Send heartbeat to master node."""
    try:
        system_info = get_system_info()
        payload = {
            "status": "online",
            **system_info,
        }

        response = await client.post(
            f"{settings.master_url}/api/v1/nodes/{settings.node_id}/heartbeat",
            json=payload,
        )

        if response.status_code == 200:
            print(f"[{datetime.now()}] Heartbeat sent successfully")
            return True
        else:
            print(f"[{datetime.now()}] Heartbeat failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"[{datetime.now()}] Heartbeat error: {e}")
        return False


async def heartbeat_loop():
    """Main heartbeat loop."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            await send_heartbeat(client)
            await asyncio.sleep(settings.heartbeat_interval)


def main():
    """Entry point for the agent."""
    print(f"Starting ML-Server-Manager Worker Agent")
    print(f"Node ID: {settings.node_id}")
    print(f"Master URL: {settings.master_url}")
    print(f"Storage Path: {settings.storage_path}")
    print(f"Heartbeat Interval: {settings.heartbeat_interval}s")

    asyncio.run(heartbeat_loop())


if __name__ == "__main__":
    main()
