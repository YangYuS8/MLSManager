"""Background task scheduler using asyncio.

Simple background task scheduler for periodic tasks without external dependencies.
For production with high reliability requirements, consider using Celery + RabbitMQ.
"""

import asyncio
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import select, update

from app.core.database import async_session_maker
from app.models.job import Job, JobStatus
from app.models.node import Node, NodeStatus

# Global task handles
_background_tasks: list[asyncio.Task] = []
_shutdown_event: asyncio.Event | None = None


async def check_offline_nodes(timeout_seconds: int = 90) -> int:
    """
    Check for nodes that haven't sent heartbeat within timeout period.
    Mark them as offline.

    Returns number of nodes marked offline.
    """
    try:
        async with async_session_maker() as db:
            threshold = datetime.now(UTC) - __import__("datetime").timedelta(
                seconds=timeout_seconds
            )

            # Find nodes that are online but haven't sent heartbeat
            result = await db.execute(
                select(Node).where(
                    Node.status == NodeStatus.ONLINE.value,
                    Node.is_active.is_(True),
                    Node.last_heartbeat < threshold,
                )
            )
            stale_nodes = result.scalars().all()

            if stale_nodes:
                node_ids = [n.node_id for n in stale_nodes]
                await db.execute(
                    update(Node)
                    .where(Node.node_id.in_(node_ids))
                    .values(status=NodeStatus.OFFLINE.value)
                )
                await db.commit()
                logger.warning(f"Marked {len(node_ids)} nodes as offline: {node_ids}")
                return len(node_ids)

            return 0

    except Exception as e:
        logger.error(f"Error checking offline nodes: {e}")
        return 0


async def check_stale_jobs(timeout_seconds: int = 7200) -> int:
    """
    Check for jobs that have been running too long without updates.
    Mark them as failed (timeout).

    Default timeout: 2 hours (7200 seconds)
    Returns number of jobs marked as timed out.
    """
    try:
        async with async_session_maker() as db:
            threshold = datetime.now(UTC) - __import__("datetime").timedelta(
                seconds=timeout_seconds
            )

            # Find jobs that are running but started too long ago
            result = await db.execute(
                select(Job).where(
                    Job.status == JobStatus.RUNNING.value,
                    Job.started_at < threshold,
                )
            )
            stale_jobs = result.scalars().all()

            count = 0
            for job in stale_jobs:
                job.status = JobStatus.FAILED.value
                job.error_message = f"Job timed out after {timeout_seconds}s"
                job.completed_at = datetime.now(UTC)
                count += 1

            if count > 0:
                await db.commit()
                logger.warning(f"Marked {count} stale jobs as failed (timeout)")

            return count

    except Exception as e:
        logger.error(f"Error checking stale jobs: {e}")
        return 0


async def cleanup_old_jobs(days: int = 30) -> int:
    """
    Clean up completed/failed/cancelled jobs older than specified days.
    This is optional maintenance task.

    Returns number of jobs deleted.
    """
    try:
        async with async_session_maker() as db:
            threshold = datetime.now(UTC) - __import__("datetime").timedelta(days=days)

            # Find old completed jobs
            result = await db.execute(
                select(Job).where(
                    Job.status.in_([
                        JobStatus.COMPLETED.value,
                        JobStatus.FAILED.value,
                        JobStatus.CANCELLED.value,
                    ]),
                    Job.completed_at < threshold,
                )
            )
            old_jobs = result.scalars().all()

            count = len(old_jobs)
            for job in old_jobs:
                await db.delete(job)

            if count > 0:
                await db.commit()
                logger.info(f"Cleaned up {count} old jobs (older than {days} days)")

            return count

    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {e}")
        return 0


async def _node_monitor_loop(interval: int = 30):
    """Background loop to monitor node status."""
    global _shutdown_event
    logger.info(f"Starting node monitor (interval: {interval}s)")

    while _shutdown_event and not _shutdown_event.is_set():
        try:
            await check_offline_nodes()
        except Exception as e:
            logger.error(f"Node monitor error: {e}")

        # Wait for interval or shutdown
        try:
            await asyncio.wait_for(
                _shutdown_event.wait(),
                timeout=interval,
            )
        except TimeoutError:
            pass  # Normal timeout, continue loop

    logger.info("Node monitor stopped")


async def _job_monitor_loop(interval: int = 60):
    """Background loop to monitor job status."""
    global _shutdown_event
    logger.info(f"Starting job monitor (interval: {interval}s)")

    while _shutdown_event and not _shutdown_event.is_set():
        try:
            await check_stale_jobs()
        except Exception as e:
            logger.error(f"Job monitor error: {e}")

        # Wait for interval or shutdown
        try:
            await asyncio.wait_for(
                _shutdown_event.wait(),
                timeout=interval,
            )
        except TimeoutError:
            pass  # Normal timeout, continue loop

    logger.info("Job monitor stopped")


async def start_background_tasks():
    """Start all background monitoring tasks."""
    global _background_tasks, _shutdown_event

    _shutdown_event = asyncio.Event()

    # Start monitor tasks
    _background_tasks = [
        asyncio.create_task(_node_monitor_loop(interval=30)),
        asyncio.create_task(_job_monitor_loop(interval=60)),
    ]

    logger.info("Background tasks started")


async def stop_background_tasks():
    """Stop all background monitoring tasks."""
    global _background_tasks, _shutdown_event

    if _shutdown_event:
        _shutdown_event.set()

    # Wait for tasks to complete
    for task in _background_tasks:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass

    _background_tasks = []
    _shutdown_event = None

    logger.info("Background tasks stopped")
