from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import AuditEventRecord
from app.schemas.audit import AuditEventSummary


def write_audit_event(
    session: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    status: str,
    source_system: str = "lis-core-api",
    actor_user_id: str | None = None,
    actor_username: str | None = None,
    actor_role_code: str | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    merged_context = dict(context or {})
    if actor_user_id is not None:
        merged_context.setdefault("actor_user_id", actor_user_id)
    if actor_username is not None:
        merged_context.setdefault("actor_username", actor_username)
    if actor_role_code is not None:
        merged_context.setdefault("actor_role_code", actor_role_code)
    session.add(
        AuditEventRecord(
            id=str(uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            status=status,
            source_system=source_system,
            context=merged_context,
        )
    )


def list_audit_events(
    session: Session,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[AuditEventSummary]:
    stmt: Select[tuple[AuditEventRecord]] = select(AuditEventRecord).order_by(
        AuditEventRecord.event_at.desc()
    )
    if entity_type:
        stmt = stmt.where(AuditEventRecord.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditEventRecord.entity_id == entity_id)
    return [
        AuditEventSummary(
            id=row.id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            action=row.action,
            status=row.status,
            source_system=row.source_system,
            event_at=row.event_at,
            context=row.context,
        )
        for row in session.scalars(stmt).all()
    ]
