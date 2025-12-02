"""Worker Agent for ML-Server-Manager.

This agent runs on worker nodes and communicates with the master node to:
- Auto-register with master and obtain agent token
- Report node status and resource usage via heartbeats
- Fetch and execute jobs (Docker/conda/venv)
- Scan and report local datasets
"""

import asyncio
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# ============================================================================
# Configuration
# ============================================================================


class AgentSettings(BaseSettings):
    """Agent configuration settings."""

    # Master node connection
    master_url: str = "http://localhost:8000"

    # Node identification
    node_name: str = "worker-001"
    node_hostname: str | None = None  # Auto-detected if not set

    # Timing
    heartbeat_interval: int = 30  # seconds
    job_poll_interval: int = 10  # seconds
    dataset_scan_interval: int = 300  # seconds (5 min)

    # Paths
    storage_path: str = "/data"
    datasets_path: str = "/data/datasets"
    jobs_workspace: str = "/data/jobs"
    log_path: str = "/var/log/ml-agent"

    # Stored agent token (persisted after registration)
    agent_token: str | None = None
    token_file: str = "/etc/ml-agent/token"

    class Config:
        env_prefix = "AGENT_"


settings = AgentSettings()


# ============================================================================
# Data Models
# ============================================================================


class JobInfo(BaseModel):
    """Job information from master."""

    id: int
    name: str
    command: str
    environment: str | None = None  # docker/conda/venv/system
    env_config: dict[str, Any] | None = None
    environment_vars: dict[str, str] | None = None
    working_directory: str | None = None
    timeout_seconds: int | None = None


class DatasetInfo(BaseModel):
    """Scanned dataset information."""

    name: str
    local_path: str
    size_bytes: int | None = None
    file_count: int | None = None
    format: str | None = None
    description: str | None = None


# ============================================================================
# System Information
# ============================================================================


def get_hostname() -> str:
    """Get system hostname."""
    import socket

    return settings.node_hostname or socket.gethostname()


def get_system_info() -> dict[str, Any]:
    """Collect system information for heartbeat."""
    info: dict[str, Any] = {
        "cpu_count": os.cpu_count(),
        "memory_total_gb": None,
        "gpu_count": 0,
        "gpu_info": None,
        "storage_total_gb": None,
        "storage_used_gb": None,
    }

    # Memory info (Linux)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb = int(line.split()[1])
                    info["memory_total_gb"] = mem_kb // (1024 * 1024)
                    break
    except Exception:
        pass

    # GPU info (nvidia-smi)
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            gpus = [g.strip() for g in result.stdout.strip().split("\n") if g.strip()]
            info["gpu_count"] = len(gpus)
            info["gpu_info"] = result.stdout.strip()
    except Exception:
        pass

    # Storage info
    try:
        if os.path.exists(settings.storage_path):
            usage = shutil.disk_usage(settings.storage_path)
            info["storage_total_gb"] = usage.total // (1024**3)
            info["storage_used_gb"] = usage.used // (1024**3)
    except Exception:
        pass

    return info


# ============================================================================
# Token Management
# ============================================================================


def load_token() -> str | None:
    """Load agent token from file."""
    if settings.agent_token:
        return settings.agent_token

    try:
        token_path = Path(settings.token_file)
        if token_path.exists():
            return token_path.read_text().strip()
    except Exception as e:
        log(f"Failed to load token: {e}")

    return None


def save_token(token: str) -> None:
    """Save agent token to file."""
    try:
        token_path = Path(settings.token_file)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(token)
        token_path.chmod(0o600)  # Owner read/write only
        log(f"Token saved to {token_path}")
    except Exception as e:
        log(f"Failed to save token: {e}")


# ============================================================================
# Logging
# ============================================================================


def log(message: str, level: str = "INFO") -> None:
    """Simple logging function."""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] [{level}] {message}", flush=True)


# ============================================================================
# Master Communication
# ============================================================================


class MasterClient:
    """Client for communicating with master node."""

    def __init__(self):
        self.base_url = settings.master_url.rstrip("/")
        self.token: str | None = load_token()
        self.node_id: int | None = None
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    @property
    def headers(self) -> dict[str, str]:
        """Get request headers with agent token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Agent-Token"] = self.token
        return headers

    async def register(self) -> bool:
        """Register with master node and obtain agent token."""
        if not self._client:
            return False

        system_info = get_system_info()
        payload = {
            "name": settings.node_name,
            "hostname": get_hostname(),
            "ip_address": None,  # Master will detect from request
            "port": 8001,  # Agent API port if we add one
            **system_info,
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/nodes/register",
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("agent_token")
                self.node_id = data.get("id")
                if self.token:
                    save_token(self.token)
                    log(f"Registered successfully. Node ID: {self.node_id}")
                    return True
            else:
                log(f"Registration failed: {response.status_code} - {response.text}", "ERROR")

        except Exception as e:
            log(f"Registration error: {e}", "ERROR")

        return False

    async def heartbeat(self) -> bool:
        """Send heartbeat to master."""
        if not self._client or not self.node_id:
            return False

        system_info = get_system_info()
        payload = {"status": "online", **system_info}

        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/nodes/{self.node_id}/heartbeat",
                json=payload,
                headers=self.headers,
            )

            if response.status_code == 200:
                log("Heartbeat sent")
                return True
            elif response.status_code == 401:
                log("Token invalid, re-registering...", "WARN")
                return await self.register()
            else:
                log(f"Heartbeat failed: {response.status_code}", "ERROR")

        except Exception as e:
            log(f"Heartbeat error: {e}", "ERROR")

        return False

    async def fetch_pending_jobs(self) -> list[JobInfo]:
        """Fetch pending jobs assigned to this node."""
        if not self._client:
            return []

        try:
            response = await self._client.get(
                f"{self.base_url}/api/v1/jobs/pending",
                headers=self.headers,
            )

            if response.status_code == 200:
                jobs_data = response.json()
                return [JobInfo(**job) for job in jobs_data]
            elif response.status_code == 401:
                log("Token invalid for job fetch", "WARN")

        except Exception as e:
            log(f"Job fetch error: {e}", "ERROR")

        return []

    async def update_job_status(
        self,
        job_id: int,
        status: str,
        exit_code: int | None = None,
        error_message: str | None = None,
    ) -> bool:
        """Update job status on master."""
        if not self._client:
            return False

        payload: dict[str, Any] = {"status": status}
        if exit_code is not None:
            payload["exit_code"] = exit_code
        if error_message:
            payload["error_message"] = error_message

        try:
            response = await self._client.patch(
                f"{self.base_url}/api/v1/jobs/{job_id}/status",
                json=payload,
                headers=self.headers,
            )
            return response.status_code == 200

        except Exception as e:
            log(f"Status update error: {e}", "ERROR")
            return False

    async def report_datasets(self, datasets: list[DatasetInfo]) -> bool:
        """Report scanned datasets to master."""
        if not self._client or not datasets:
            return True

        payload = {"datasets": [d.model_dump() for d in datasets]}

        try:
            response = await self._client.post(
                f"{self.base_url}/api/v1/datasets/batch",
                json=payload,
                headers=self.headers,
            )

            if response.status_code == 200:
                result = response.json()
                log(
                    f"Datasets reported: {result.get('registered', 0)} new, "
                    f"{result.get('updated', 0)} updated"
                )
                return True

        except Exception as e:
            log(f"Dataset report error: {e}", "ERROR")

        return False


# ============================================================================
# Job Execution
# ============================================================================


class JobExecutor:
    """Execute jobs in various environments."""

    def __init__(self, client: MasterClient):
        self.client = client
        self.running_jobs: dict[int, asyncio.subprocess.Process] = {}

    async def execute(self, job: JobInfo) -> tuple[int, str | None]:
        """
        Execute a job and return (exit_code, error_message).

        Supports environments:
        - docker: Run in Docker container
        - conda: Run in conda environment
        - venv: Run in Python venv
        - system/None: Run directly in system shell
        """
        log(f"Starting job {job.id}: {job.name}")

        # Notify master that job is running
        await self.client.update_job_status(job.id, "running")

        # Prepare working directory
        workdir = job.working_directory or os.path.join(
            settings.jobs_workspace, f"job_{job.id}"
        )
        os.makedirs(workdir, exist_ok=True)

        # Prepare environment variables
        env = os.environ.copy()
        if job.environment_vars:
            env.update(job.environment_vars)

        try:
            if job.environment == "docker":
                exit_code, error = await self._run_docker(job, workdir, env)
            elif job.environment == "conda":
                exit_code, error = await self._run_conda(job, workdir, env)
            elif job.environment == "venv":
                exit_code, error = await self._run_venv(job, workdir, env)
            else:
                exit_code, error = await self._run_system(job, workdir, env)

            return exit_code, error

        except TimeoutError:
            return -1, f"Job timed out after {job.timeout_seconds}s"
        except Exception as e:
            return -1, str(e)

    async def _run_system(
        self, job: JobInfo, workdir: str, env: dict
    ) -> tuple[int, str | None]:
        """Run job directly in system shell."""
        proc = await asyncio.create_subprocess_shell(
            job.command,
            cwd=workdir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.running_jobs[job.id] = proc

        try:
            timeout = job.timeout_seconds or 3600  # Default 1 hour
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            if proc.returncode != 0:
                return proc.returncode, stderr.decode()[:1000] if stderr else None
            return 0, None

        finally:
            self.running_jobs.pop(job.id, None)

    async def _run_docker(
        self, job: JobInfo, workdir: str, env: dict
    ) -> tuple[int, str | None]:
        """Run job in Docker container."""
        config = job.env_config or {}
        image = config.get("image", "python:3.12")
        volumes = config.get("volumes", [])
        gpu = config.get("gpu", False)

        # Build docker run command
        cmd_parts = ["docker", "run", "--rm"]

        # Add volume mounts
        cmd_parts.extend(["-v", f"{workdir}:/workspace"])
        for vol in volumes:
            cmd_parts.extend(["-v", vol])

        # Add GPU support
        if gpu:
            cmd_parts.extend(["--gpus", "all"])

        # Add environment variables
        for key, value in (job.environment_vars or {}).items():
            cmd_parts.extend(["-e", f"{key}={value}"])

        # Set working directory and image
        cmd_parts.extend(["-w", "/workspace", image])

        # Add command
        cmd_parts.extend(["sh", "-c", job.command])

        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.running_jobs[job.id] = proc

        try:
            timeout = job.timeout_seconds or 3600
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            if proc.returncode != 0:
                return proc.returncode, stderr.decode()[:1000] if stderr else None
            return 0, None

        finally:
            self.running_jobs.pop(job.id, None)

    async def _run_conda(
        self, job: JobInfo, workdir: str, env: dict
    ) -> tuple[int, str | None]:
        """Run job in conda environment."""
        config = job.env_config or {}
        conda_env = config.get("env_name", "base")

        # Wrap command with conda activation
        wrapped_cmd = f"source $(conda info --base)/etc/profile.d/conda.sh && conda activate {conda_env} && {job.command}"

        proc = await asyncio.create_subprocess_shell(
            wrapped_cmd,
            cwd=workdir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            executable="/bin/bash",
        )

        self.running_jobs[job.id] = proc

        try:
            timeout = job.timeout_seconds or 3600
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            if proc.returncode != 0:
                return proc.returncode, stderr.decode()[:1000] if stderr else None
            return 0, None

        finally:
            self.running_jobs.pop(job.id, None)

    async def _run_venv(
        self, job: JobInfo, workdir: str, env: dict
    ) -> tuple[int, str | None]:
        """Run job in Python venv."""
        config = job.env_config or {}
        venv_path = config.get("venv_path", ".venv")

        # Resolve venv path
        if not os.path.isabs(venv_path):
            venv_path = os.path.join(workdir, venv_path)

        # Wrap command with venv activation
        activate_script = os.path.join(venv_path, "bin", "activate")
        wrapped_cmd = f"source {activate_script} && {job.command}"

        proc = await asyncio.create_subprocess_shell(
            wrapped_cmd,
            cwd=workdir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            executable="/bin/bash",
        )

        self.running_jobs[job.id] = proc

        try:
            timeout = job.timeout_seconds or 3600
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            if proc.returncode != 0:
                return proc.returncode, stderr.decode()[:1000] if stderr else None
            return 0, None

        finally:
            self.running_jobs.pop(job.id, None)

    async def cancel(self, job_id: int) -> bool:
        """Cancel a running job."""
        proc = self.running_jobs.get(job_id)
        if proc:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=10)
            except TimeoutError:
                proc.kill()
            return True
        return False


# ============================================================================
# Dataset Scanner
# ============================================================================


class DatasetScanner:
    """Scan local directories for datasets."""

    DATASET_FORMATS = {
        ".csv": "csv",
        ".parquet": "parquet",
        ".json": "json",
        ".jsonl": "jsonl",
        ".tfrecord": "tfrecord",
        ".tar": "archive",
        ".tar.gz": "archive",
        ".zip": "archive",
    }

    def scan(self, base_path: str) -> list[DatasetInfo]:
        """
        Scan directory for datasets.

        Assumes each subdirectory is a dataset.
        """
        datasets: list[DatasetInfo] = []
        base = Path(base_path)

        if not base.exists():
            log(f"Dataset path does not exist: {base_path}", "WARN")
            return datasets

        try:
            for item in base.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    dataset = self._scan_directory(item)
                    if dataset:
                        datasets.append(dataset)

        except PermissionError as e:
            log(f"Permission denied scanning {base_path}: {e}", "ERROR")

        return datasets

    def _scan_directory(self, path: Path) -> DatasetInfo | None:
        """Scan a single directory as a dataset."""
        try:
            size_bytes = 0
            file_count = 0
            formats_found: dict[str, int] = {}

            for item in path.rglob("*"):
                if item.is_file():
                    file_count += 1
                    try:
                        size_bytes += item.stat().st_size
                    except OSError:
                        pass

                    # Detect format
                    suffix = item.suffix.lower()
                    for ext, fmt in self.DATASET_FORMATS.items():
                        if item.name.endswith(ext):
                            formats_found[fmt] = formats_found.get(fmt, 0) + 1
                            break
                    else:
                        # Check for image formats
                        if suffix in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}:
                            formats_found["images"] = formats_found.get("images", 0) + 1

            # Determine primary format
            primary_format = None
            if formats_found:
                primary_format = max(formats_found.items(), key=lambda x: x[1])[0]

            return DatasetInfo(
                name=path.name,
                local_path=str(path.absolute()),
                size_bytes=size_bytes,
                file_count=file_count,
                format=primary_format,
                description=f"Auto-scanned dataset with {file_count} files",
            )

        except Exception as e:
            log(f"Error scanning {path}: {e}", "ERROR")
            return None


# ============================================================================
# Main Agent Loop
# ============================================================================


async def agent_main():
    """Main agent loop."""
    log("Starting ML-Server-Manager Worker Agent")
    log(f"Node Name: {settings.node_name}")
    log(f"Master URL: {settings.master_url}")
    log(f"Storage Path: {settings.storage_path}")

    async with MasterClient() as client:
        # Initial registration
        if not client.token:
            log("No token found, registering with master...")
            for attempt in range(5):
                if await client.register():
                    break
                log(f"Registration attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(5)
            else:
                log("Failed to register after 5 attempts", "FATAL")
                sys.exit(1)

        # Create job executor and dataset scanner
        executor = JobExecutor(client)
        scanner = DatasetScanner()

        # Track last dataset scan time
        last_dataset_scan = 0.0

        # Main loop
        while True:
            try:
                # Send heartbeat
                await client.heartbeat()

                # Fetch and execute pending jobs
                jobs = await client.fetch_pending_jobs()
                for job in jobs:
                    log(f"Executing job {job.id}: {job.name}")
                    exit_code, error = await executor.execute(job)

                    if exit_code == 0:
                        await client.update_job_status(job.id, "completed", exit_code=0)
                        log(f"Job {job.id} completed successfully")
                    else:
                        await client.update_job_status(
                            job.id, "failed", exit_code=exit_code, error_message=error
                        )
                        log(f"Job {job.id} failed: {error}", "ERROR")

                # Periodic dataset scan
                now = asyncio.get_event_loop().time()
                if now - last_dataset_scan > settings.dataset_scan_interval:
                    log("Scanning datasets...")
                    datasets = scanner.scan(settings.datasets_path)
                    if datasets:
                        await client.report_datasets(datasets)
                    last_dataset_scan = now

            except Exception as e:
                log(f"Agent loop error: {e}", "ERROR")

            # Sleep before next iteration
            await asyncio.sleep(settings.job_poll_interval)


def main():
    """Entry point for the agent."""
    try:
        asyncio.run(agent_main())
    except KeyboardInterrupt:
        log("Agent stopped by user")
    except Exception as e:
        log(f"Agent crashed: {e}", "FATAL")
        sys.exit(1)


if __name__ == "__main__":
    main()
