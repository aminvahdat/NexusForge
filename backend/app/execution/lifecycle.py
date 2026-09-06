from datetime import datetime
from app.execution.state import ExecutionState, ExecutionStatus
from app.execution.events import Event, EventType


class ExecutionLifecycle:
    @staticmethod
    def transition(state: ExecutionState, new_status: ExecutionStatus, message: str) -> Event:
        previous = state.status.value
        state.status = new_status
        event = Event(
            event_type=EventType.EXECUTION_PROGRESS,
            message=f"{message} ({previous} → {new_status.value})",
            execution_id=state.execution_id,
            worker_id=state.worker_id,
            task_id=state.task_id,
            metadata={"previous_status": previous, "new_status": new_status.value},
        )
        state.events.append(event)
        return event

    @staticmethod
    def create_execution(execution_id: str, task_id: str) -> tuple[ExecutionState, Event]:
        state = ExecutionState(execution_id=execution_id, task_id=task_id)
        event = Event(
            event_type=EventType.EXECUTION_CREATED,
            message="Execution created",
            execution_id=execution_id,
            task_id=task_id,
        )
        state.events.append(event)
        return state, event

    @staticmethod
    def start_execution(state: ExecutionState, worker_id: str) -> Event:
        state.worker_id = worker_id
        state.status = ExecutionStatus.RUNNING
        state.started_at = datetime.utcnow()
        event = Event(
            event_type=EventType.EXECUTION_STARTED,
            message=f"Execution started on worker {worker_id}",
            execution_id=state.execution_id,
            worker_id=worker_id,
            task_id=state.task_id,
        )
        state.events.append(event)
        return event

    @staticmethod
    def complete_execution(state: ExecutionState, result: str = None) -> Event:
        state.status = ExecutionStatus.COMPLETED
        state.result = result
        state.completed_at = datetime.utcnow()
        event = Event(
            event_type=EventType.EXECUTION_COMPLETED,
            message="Execution completed",
            execution_id=state.execution_id,
            worker_id=state.worker_id,
            task_id=state.task_id,
            metadata={"result": result},
        )
        state.events.append(event)
        return event

    @staticmethod
    def fail_execution(state: ExecutionState, error: str) -> Event:
        state.status = ExecutionStatus.FAILED
        state.error = error
        state.completed_at = datetime.utcnow()
        event = Event(
            event_type=EventType.EXECUTION_FAILED,
            message=f"Execution failed: {error}",
            execution_id=state.execution_id,
            worker_id=state.worker_id,
            task_id=state.task_id,
            metadata={"error": error},
        )
        state.events.append(event)
        return event