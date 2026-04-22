from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OrderItemRecord, SpecimenRecord, TaskRecord
from app.schemas.auth import UserSummary
from app.schemas.tasks import CreateTaskRequest, TaskActionRequest, TaskFocusType, TaskSummary
from app.services.audit import write_audit_event

TERMINAL_TASK_STATUSES = {"completed", "failed", "cancelled"}


def create_task(
    session: Session,
    payload: CreateTaskRequest,
    *,
    actor: UserSummary | None = None,
) -> TaskSummary:
    _validate_task_focus(session, payload.focus_type, payload.focus_id)

    task = TaskRecord(
        id=str(uuid4()),
        group_identifier=payload.group_identifier,
        based_on_order_item_id=_optional_uuid(payload.based_on_order_item_id),
        focus_type=payload.focus_type.value,
        focus_id=str(payload.focus_id),
        queue_code=payload.queue_code,
        status=payload.status,
        business_status=payload.business_status,
        priority=payload.priority,
        owner_user_id=_optional_uuid(payload.owner_user_id),
        owner_practitioner_role_id=_optional_uuid(payload.owner_practitioner_role_id),
        device_id=_optional_uuid(payload.device_id),
        due_at=payload.due_at,
        inputs_payload=payload.inputs,
    )
    session.add(task)
    write_audit_event(
        session,
        entity_type="task",
        entity_id=task.id,
        action="create",
        status=task.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"focus_type": task.focus_type, "focus_id": task.focus_id},
    )
    session.commit()
    session.refresh(task)
    return _to_task_summary(task)


def list_tasks(
    session: Session,
    *,
    queue: str | None = None,
    status_filter: str | None = None,
    owner_user_id: UUID | None = None,
) -> list[TaskSummary]:
    stmt = select(TaskRecord).order_by(TaskRecord.authored_on.desc())
    if queue:
        stmt = stmt.where(TaskRecord.queue_code == queue)
    if status_filter:
        stmt = stmt.where(TaskRecord.status == status_filter)
    if owner_user_id:
        stmt = stmt.where(TaskRecord.owner_user_id == str(owner_user_id))
    return [_to_task_summary(task) for task in session.scalars(stmt).all()]


def claim_task(
    session: Session,
    task_id: UUID,
    payload: TaskActionRequest,
    *,
    actor: UserSummary | None = None,
) -> TaskSummary:
    task = _get_task_or_404(session, task_id)
    _require_not_terminal(task, "claim")
    task.owner_user_id = _optional_uuid(payload.owner_user_id) or task.owner_user_id
    task.owner_practitioner_role_id = (
        _optional_uuid(payload.owner_practitioner_role_id) or task.owner_practitioner_role_id
    )
    task.business_status = payload.business_status or "claimed"
    if task.status == "created":
        task.status = "ready"
    _merge_outputs(task, payload)
    if actor and task.owner_user_id is None:
        task.owner_user_id = str(actor.id)
    _commit_task_action(
        session,
        task=task,
        action="claim",
        actor=actor,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    return _to_task_summary(task)


def start_task(
    session: Session,
    task_id: UUID,
    payload: TaskActionRequest | None,
    *,
    actor: UserSummary | None = None,
) -> TaskSummary:
    task = _get_task_or_404(session, task_id)
    if task.status not in {"created", "ready", "on_hold"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot start task while it is in status '{task.status}'.",
        )
    payload = payload or TaskActionRequest()
    task.owner_user_id = _optional_uuid(payload.owner_user_id) or task.owner_user_id
    task.owner_practitioner_role_id = (
        _optional_uuid(payload.owner_practitioner_role_id) or task.owner_practitioner_role_id
    )
    task.business_status = payload.business_status or task.business_status
    task.status = "in_progress"
    task.started_at = datetime.now(UTC)
    _merge_outputs(task, payload)
    if actor and task.owner_user_id is None:
        task.owner_user_id = str(actor.id)
    _commit_task_action(
        session,
        task=task,
        action="start",
        actor=actor,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    return _to_task_summary(task)


def pause_task(
    session: Session,
    task_id: UUID,
    payload: TaskActionRequest,
    *,
    actor: UserSummary | None = None,
) -> TaskSummary:
    task = _get_task_or_404(session, task_id)
    if task.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot pause task while it is in status '{task.status}'.",
        )
    task.status = "on_hold"
    task.business_status = payload.business_status or task.business_status
    _merge_outputs(task, payload)
    _commit_task_action(
        session,
        task=task,
        action="pause",
        actor=actor,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    return _to_task_summary(task)


def complete_task(
    session: Session,
    task_id: UUID,
    payload: TaskActionRequest | None,
    *,
    actor: UserSummary | None = None,
) -> TaskSummary:
    task = _get_task_or_404(session, task_id)
    _require_not_terminal(task, "complete")
    payload = payload or TaskActionRequest()
    task.status = "completed"
    task.business_status = payload.business_status or task.business_status
    task.completed_at = datetime.now(UTC)
    _merge_outputs(task, payload)
    _commit_task_action(
        session,
        task=task,
        action="complete",
        actor=actor,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    return _to_task_summary(task)


def fail_task(
    session: Session,
    task_id: UUID,
    payload: TaskActionRequest,
    *,
    actor: UserSummary | None = None,
) -> TaskSummary:
    task = _get_task_or_404(session, task_id)
    _require_not_terminal(task, "fail")
    if not payload.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failing a task requires a reason.",
        )
    task.status = "failed"
    task.business_status = payload.business_status or task.business_status
    task.failed_reason = payload.reason
    task.completed_at = datetime.now(UTC)
    _merge_outputs(task, payload)
    _commit_task_action(
        session,
        task=task,
        action="fail",
        actor=actor,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    return _to_task_summary(task)


def _validate_task_focus(session: Session, focus_type: TaskFocusType, focus_id: UUID) -> None:
    if focus_type is TaskFocusType.ORDER_ITEM and session.get(OrderItemRecord, str(focus_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item {focus_id} was not found for task focus.",
        )
    if focus_type is TaskFocusType.SPECIMEN and session.get(SpecimenRecord, str(focus_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specimen {focus_id} was not found for task focus.",
        )


def _get_task_or_404(session: Session, task_id: UUID) -> TaskRecord:
    task = session.get(TaskRecord, str(task_id))
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} was not found.",
        )
    return task


def _require_not_terminal(task: TaskRecord, action: str) -> None:
    if task.status in TERMINAL_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot {action} task while it is in status '{task.status}'.",
        )


def _merge_outputs(task: TaskRecord, payload: TaskActionRequest) -> None:
    if payload.outputs:
        task.outputs_payload = {**task.outputs_payload, **payload.outputs}


def _commit_task_action(
    session: Session,
    *,
    task: TaskRecord,
    action: str,
    actor: UserSummary | None,
    context: dict[str, object | None],
) -> None:
    write_audit_event(
        session,
        entity_type="task",
        entity_id=task.id,
        action=action,
        status=task.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context=context,
    )
    session.commit()
    session.refresh(task)


def _optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None


def _to_task_summary(task: TaskRecord) -> TaskSummary:
    return TaskSummary(
        id=task.id,
        group_identifier=task.group_identifier,
        based_on_order_item_id=task.based_on_order_item_id,
        focus_type=task.focus_type,
        focus_id=task.focus_id,
        queue_code=task.queue_code,
        status=task.status,
        business_status=task.business_status,
        priority=task.priority,
        owner_user_id=task.owner_user_id,
        authored_on=task.authored_on,
        due_at=task.due_at,
    )
