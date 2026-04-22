from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.helpers import raise_not_implemented
from app.schemas.common import ApiError
from app.schemas.tasks import CreateTaskRequest, TaskActionRequest, TaskSummary

router = APIRouter(prefix="/api/v1", tags=["tasks"])
NOT_IMPLEMENTED = {
    status.HTTP_501_NOT_IMPLEMENTED: {
        "model": ApiError,
        "description": "Route exists, but workflow logic is not implemented yet.",
    }
}


@router.post(
    "/tasks",
    response_model=TaskSummary,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_IMPLEMENTED,
)
def create_task(payload: CreateTaskRequest) -> TaskSummary:
    del payload
    raise_not_implemented("Task creation")


@router.get("/tasks", response_model=dict[str, list[TaskSummary]], responses=NOT_IMPLEMENTED)
def list_tasks(
    queue: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    owner_user_id: UUID | None = None,
) -> dict[str, list[TaskSummary]]:
    del queue, status_filter, owner_user_id
    raise_not_implemented("Task search")


@router.post("/tasks/{task_id}/claim", response_model=TaskSummary, responses=NOT_IMPLEMENTED)
def claim_task(task_id: UUID, payload: TaskActionRequest) -> TaskSummary:
    del task_id, payload
    raise_not_implemented("Task claim")


@router.post("/tasks/{task_id}/start", response_model=TaskSummary, responses=NOT_IMPLEMENTED)
def start_task(task_id: UUID, payload: TaskActionRequest | None = None) -> TaskSummary:
    del task_id, payload
    raise_not_implemented("Task start")


@router.post("/tasks/{task_id}/pause", response_model=TaskSummary, responses=NOT_IMPLEMENTED)
def pause_task(task_id: UUID, payload: TaskActionRequest) -> TaskSummary:
    del task_id, payload
    raise_not_implemented("Task pause")


@router.post("/tasks/{task_id}/complete", response_model=TaskSummary, responses=NOT_IMPLEMENTED)
def complete_task(task_id: UUID, payload: TaskActionRequest | None = None) -> TaskSummary:
    del task_id, payload
    raise_not_implemented("Task completion")


@router.post("/tasks/{task_id}/fail", response_model=TaskSummary, responses=NOT_IMPLEMENTED)
def fail_task(task_id: UUID, payload: TaskActionRequest) -> TaskSummary:
    del task_id, payload
    raise_not_implemented("Task failure")

