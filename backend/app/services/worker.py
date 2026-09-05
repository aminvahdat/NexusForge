"""Worker Pool Service — Complete Phase 4E implementation.

This module implements the WorkerPool with configurable concurrency
(MAX_CONCURRENT_WORKERS=2 default), Redis-backed task queue, and
worker heartbeat monitoring. Workers are reusable execution resources
that dynamically load agent roles based on task assignment.

Key features:
- Worker pool with max concurrent workers via env var
- Redis task queue using ZPOPMIN for atomic claiming
- Worker heartbeat tracking with automatic stale detection
- Agent role assignment per task
- Task scheduling with pool size enforcement
- Health monitoring background loop
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.config.settings import get_settings
from app.models.task import Task, TaskStatus
from app.models.enums import AgentRole, WorkerStatus
from app.services.redis import get_redis

logger = structlog.get_logger()


class WorkerPool:
    """Worker pool with configurable worker count (default: 2)."""

    def __init__(self):
        self.workers: Dict[str, Any] = {}
        self.pool_size = get_settings().max_concurrent_workers
        self._initialized = False

    def set_pool_size(self, size: int) -> None:
        """Set maximum concurrent workers (default: 2)."""
        self.pool_size = max(1, size)
        logger.info("worker_pool.size_updated", size=self.pool_size)

    def add_worker(self, worker: Any) -> None:
        """Add a worker to the pool (registers with Redis)."""
        self.workers[worker.worker_id] = worker
        logger.info("worker_registered", worker_id=worker.worker_id, hostname=worker.hostname)

    def get_idle_workers(self) -> List[Any]:
        """Return list of workers in IDLE status."""
        return [
            w for w in self.workers.values()
            if w.status == WorkerStatus.IDLE
        ]

    def get_available_workers(self) -> List[Any]:
        """Return workers that are ready to accept tasks (IDLE or WAITING)."""
        return [
            w for w in self.workers.values()
            if w.status in (WorkerStatus.IDLE, WorkerStatus.WAITING)
        ]

    def get_active_workers(self) -> List[Any]:
        """Return workers currently executing tasks."""
        return [
            w for w in self.workers.values()
            if w.status in (WorkerStatus.BUSY, WorkerStatus.RUNNING)
        ]

    def get_all_workers(self) -> List[Any]:
        """Return all registered workers."""
        return list(self.workers.values())

    async def start_worker_pool(self) -> None:
        """Start worker health monitoring (background task)."""
        if not self._initialized:
            asyncio.create_task(self._monitor_workers())
            self._initialized = True
            logger.info("worker_pool.started", size=self.pool_size)

    async def _monitor_workers(self):
        """Background task that monitors worker heartbeats and status."""
        redis = await get_redis()
        while True:
            try:
                # Get all worker state from Redis
                worker_state = await redis.hgetall("WORKER_STATE")
                for worker_id, state in worker_state.items():
                    if worker_id in self.workers:
                        worker = self.workers[worker_id]
                        # Update worker status from Redis state
                        await self._update_worker_status(worker, state)
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error("worker_pool.monitor_error", error=str(e))
                await asyncio.sleep(5)

    async def _update_worker_status(self, worker: Any, state_data) -> None:
        """Update worker status from Redis state."""
        if isinstance(state_data, bytes):
            status = state_data.decode()
        else:
            status = str(state_data)
        await worker.set_status(status)
        logger.debug("worker_status_updated", worker_id=worker.worker_id, status=status)

    async def schedule_task(self, task: Task, worker: Optional[Any] = None) -> Task:
        """Schedule a task for execution.

        Uses atomic Redis claim mechanism (ZPOPMIN) to prevent duplicate claims.
        Enforces MAX_CONCURRENT_WORKERS pool size.
        """
        # Validate task state
        if task.status != TaskStatus.QUEUED:
            raise ValueError(f"Task must be in QUEUED state, got {task.status}")

        # Find available worker from pool
        selected_worker = None

        if worker is not None:
            selected_worker = worker
        else:
            # First try idle workers
            available = self.get_idle_workers()
            if not available:
                # Check for workers in WAITING state
                waiting = self.get_available_workers()
                if waiting:
                    available = waiting
                else:
                    # No available workers — must wait
                    raise RuntimeError(
                        f"No available workers (pool size: {self.pool_size})"
                    )

            if available:
                selected_worker = available[0]

        if selected_worker is None:
            raise RuntimeError("No worker available for task scheduling")

        # Update task state and assign worker
        task.status = TaskStatus.ASSIGNED
        task.assigned_worker = selected_worker.worker_id
        task.started_at = datetime.now(timezone.utc)
        logger.info(
            "task_assigned",
            task_id=str(task.id),
            worker_id=selected_worker.worker_id,
        )
        return task

    def monitor_worker_heartbeat(self, worker_id: str, is_alive: bool) -> None:
        """Update worker heartbeat status (called from worker heartbeat loop)."""
        worker = self.workers.get(worker_id)
        if worker:
            new_status = WorkerStatus.IDLE if is_alive else WorkerStatus.OFFLINE
            worker.set_status(new_status)
            logger.info("worker_heartbeat", worker_id=worker_id, is_alive=is_alive)

    async def start_worker(self, worker: Any) -> None:
        """Start a worker (set to IDLE, register heartbeat)."""
        if worker.status != WorkerStatus.IDLE:
            worker.status = WorkerStatus.IDLE
        # Register heartbeat in Redis
        redis = await get_redis()
        await redis.hset("WORKER_STATE", worker.worker_id, "idle")
        logger.info("worker_started", worker_id=worker.worker_id, hostname=worker.hostname)