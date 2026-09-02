"""Chief Orchestrator — the central coordinator of NexusForge."""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ChiefOrchestrator:
    """Coordinates the entire NexusForge workflow."""

    def __init__(self, max_concurrent_workers: int = 2):
        self.max_concurrent_workers = max_concurrent_workers
        self.tasks: dict[int, dict] = {}  # task_id -> task_state + metadata
        self.workers: list[asyncio.Task] = []
        self.projects: dict[str, dict] = {}

    async def create_task(self, task_id: int, title: str, description: str, 
                         dependencies: list[int] = None) -> int:
        """Register a new task in the orchestration system."""
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "state": TaskState.QUEUED,
            "dependencies": dependencies or [],
            "created_at": datetime.utcnow().isoformat(),
            "assigned_worker": None,
        }
        self.tasks[task_id] = task
        return task_id

    async def assign_worker(self, task_id: int, worker_id: int) -> bool:
        """Assign a task to a worker if capacity allows."""
        if len(self.workers) >= self.max_concurrent_workers:
            return False
        self.workers.append(asyncio.create_task(self._execute_task(task_id)))
        return True

    async def _execute_task(self, task_id: int) -> None:
        """Execute a task to completion or mark as failed."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Wait for dependencies
        for dep_id in task.get("dependencies", []):
            if task_id not in self.tasks.get(dep_id, {}) or self.tasks[dep_id]["state"] != TaskState.COMPLETED:
                await asyncio.sleep(1)
                continue

        # Assign to a worker
        if not await self.assign_worker(task_id, len(self.workers)):
            task["state"] = TaskState.BLOCKED
            return

        # Simulate work execution
        try:
            # In a real implementation, this would invoke the appropriate agent
            await asyncio.sleep(2)  # simulate work
            task["state"] = TaskState.COMPLETED
        except Exception as e:
            task["state"] = TaskState.FAILED
            raise e

    async def get_task_status(self, task_id: int) -> Optional[dict]:
        """Retrieve the current status of a task."""
        return self.tasks.get(task_id)

    async def list_tasks(self) -> list[dict]:
        """List all tasks with their current states."""
        return [{**task, "state": task["state"]} for task in self.tasks.values()]

    async def cancel_task(self, task_id: int) -> bool:
        """Cancel a running task."""
        task = self.tasks.get(task_id)
        if task and task["state"] == TaskState.RUNNING:
            task["state"] = TaskState.CANCELLED
            return True
        return False
