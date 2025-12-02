"""Job service for job scheduling and management."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.models.node import Node, NodeStatus


class JobService:
    """Service for job scheduling and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign_job_to_node(self, job: Job) -> Node | None:
        """
        Assign a job to the best available node based on resource requirements.
        Returns the assigned node or None if no suitable node found.
        """
        # Build query for available nodes
        query = select(Node).where(
            Node.status == NodeStatus.ONLINE.value,
            Node.is_active.is_(True),
        )

        # Filter by resource requirements
        if job.gpu_count and job.gpu_count > 0:
            query = query.where(Node.gpu_count >= job.gpu_count)

        if job.memory_limit_gb:
            query = query.where(Node.memory_total_gb >= job.memory_limit_gb)

        if job.cpu_limit:
            query = query.where(Node.cpu_count >= job.cpu_limit)

        result = await self.db.execute(query)
        candidates = result.scalars().all()

        if not candidates:
            return None

        # Simple load balancing: pick node with least running jobs
        best_node = None
        min_jobs = float("inf")

        for node in candidates:
            # Count running jobs on this node
            job_count_result = await self.db.execute(
                select(func.count(Job.id)).where(
                    Job.node_id == node.id,
                    Job.status == JobStatus.RUNNING.value,
                )
            )
            running_jobs = job_count_result.scalar() or 0

            if running_jobs < min_jobs:
                min_jobs = running_jobs
                best_node = node

        if best_node:
            job.node_id = best_node.id
            job.status = JobStatus.QUEUED.value
            await self.db.commit()
            await self.db.refresh(job)

        return best_node

    async def get_pending_jobs_for_node(
        self, node_id: str, limit: int = 10
    ) -> list[Job]:
        """Get queued jobs assigned to a specific node."""
        # First get the node's internal ID
        node_result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = node_result.scalar_one_or_none()
        if not node:
            return []

        result = await self.db.execute(
            select(Job)
            .where(
                Job.node_id == node.id,
                Job.status == JobStatus.QUEUED.value,
            )
            .order_by(Job.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_job_status(
        self,
        job_id: int,
        status: JobStatus,
        exit_code: int | None = None,
        error_message: str | None = None,
        log_path: str | None = None,
        output_path: str | None = None,
    ) -> Job | None:
        """Update job status and related fields."""
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return None

        job.status = status.value

        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.now(UTC)

        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now(UTC)

        if exit_code is not None:
            job.exit_code = exit_code
        if error_message:
            job.error_message = error_message
        if log_path:
            job.log_path = log_path
        if output_path:
            job.output_path = output_path

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job_stats(self) -> dict:
        """Get aggregated job statistics."""
        stats = {
            "total_jobs": 0,
            "pending_jobs": 0,
            "queued_jobs": 0,
            "running_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
        }

        # Get counts for each status
        for status in JobStatus:
            result = await self.db.execute(
                select(func.count(Job.id)).where(Job.status == status.value)
            )
            count = result.scalar() or 0
            stats[f"{status.value}_jobs"] = count
            stats["total_jobs"] += count

        return stats

    async def auto_assign_pending_jobs(self) -> int:
        """Auto-assign all pending jobs to available nodes. Returns count of assigned jobs."""
        result = await self.db.execute(
            select(Job)
            .where(Job.status == JobStatus.PENDING.value)
            .order_by(Job.created_at)
        )
        pending_jobs = result.scalars().all()

        assigned_count = 0
        for job in pending_jobs:
            node = await self.assign_job_to_node(job)
            if node:
                assigned_count += 1

        return assigned_count
