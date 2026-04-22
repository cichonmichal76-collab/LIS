from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.tasks import CreateTaskRequest, TaskActionRequest, TaskSummary
from app.services import tasks as task_service

router = APIRouter(prefix="/api/v1", tags=["tasks"])


@router.post(
    "/tasks",
    response_model=TaskSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: CreateTaskRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
        )
    ),
) -> TaskSummary:
    return task_service.create_task(session, payload, actor=current_user)


@router.get("/tasks", response_model=dict[str, list[TaskSummary]])
def list_tasks(
    session: DbSession,
    queue: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    owner_user_id: UUID | None = None,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[TaskSummary]]:
    return {
        "items": task_service.list_tasks(
            session,
            queue=queue,
            status_filter=status_filter,
            owner_user_id=owner_user_id,
        )
    }


@router.post("/tasks/{task_id}/claim", response_model=TaskSummary)
def claim_task(
    task_id: UUID,
    payload: TaskActionRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
        )
    ),
) -> TaskSummary:
    return task_service.claim_task(session, task_id, payload, actor=current_user)


@router.post("/tasks/{task_id}/start", response_model=TaskSummary)
def start_task(
    task_id: UUID,
    session: DbSession,
    payload: TaskActionRequest | None = None,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
        )
    ),
) -> TaskSummary:
    return task_service.start_task(session, task_id, payload, actor=current_user)


@router.post("/tasks/{task_id}/pause", response_model=TaskSummary)
def pause_task(
    task_id: UUID,
    payload: TaskActionRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
        )
    ),
) -> TaskSummary:
    return task_service.pause_task(session, task_id, payload, actor=current_user)


@router.post("/tasks/{task_id}/complete", response_model=TaskSummary)
def complete_task(
    task_id: UUID,
    session: DbSession,
    payload: TaskActionRequest | None = None,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
        )
    ),
) -> TaskSummary:
    return task_service.complete_task(session, task_id, payload, actor=current_user)


@router.post("/tasks/{task_id}/fail", response_model=TaskSummary)
def fail_task(
    task_id: UUID,
    payload: TaskActionRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
        )
    ),
) -> TaskSummary:
    return task_service.fail_task(session, task_id, payload, actor=current_user)
