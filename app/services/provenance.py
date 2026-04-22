from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import ProvenanceRecord
from app.schemas.audit import ProvenanceRecordSummary


def write_provenance_record(
    session: Session,
    *,
    target_resource_type: str,
    target_resource_id: str,
    activity_code: str,
    based_on_order_id: str | None = None,
    based_on_order_item_id: str | None = None,
    specimen_id: str | None = None,
    observation_id: str | None = None,
    report_version_id: str | None = None,
    device_id: str | None = None,
    agent_user_id: str | None = None,
    agent_practitioner_role_id: str | None = None,
    inputs: dict[str, Any] | None = None,
    signature: dict[str, Any] | None = None,
) -> None:
    session.add(
        ProvenanceRecord(
            id=str(uuid4()),
            target_resource_type=target_resource_type,
            target_resource_id=target_resource_id,
            activity_code=activity_code,
            based_on_order_id=based_on_order_id,
            based_on_order_item_id=based_on_order_item_id,
            specimen_id=specimen_id,
            observation_id=observation_id,
            report_version_id=report_version_id,
            device_id=device_id,
            agent_user_id=agent_user_id,
            agent_practitioner_role_id=agent_practitioner_role_id,
            inputs=inputs or {},
            signature=signature or {},
        )
    )


def list_provenance_records(
    session: Session,
    *,
    target_resource_type: str | None = None,
    target_resource_id: str | None = None,
) -> list[ProvenanceRecordSummary]:
    stmt: Select[tuple[ProvenanceRecord]] = select(ProvenanceRecord).order_by(
        ProvenanceRecord.recorded_at.desc()
    )
    if target_resource_type:
        stmt = stmt.where(ProvenanceRecord.target_resource_type == target_resource_type)
    if target_resource_id:
        stmt = stmt.where(ProvenanceRecord.target_resource_id == target_resource_id)
    return [
        ProvenanceRecordSummary(
            id=row.id,
            target_resource_type=row.target_resource_type,
            target_resource_id=row.target_resource_id,
            activity_code=row.activity_code,
            based_on_order_id=row.based_on_order_id,
            based_on_order_item_id=row.based_on_order_item_id,
            specimen_id=row.specimen_id,
            observation_id=row.observation_id,
            report_version_id=row.report_version_id,
            device_id=row.device_id,
            agent_user_id=row.agent_user_id,
            agent_practitioner_role_id=row.agent_practitioner_role_id,
            recorded_at=row.recorded_at,
            inputs=row.inputs,
            signature=row.signature,
        )
        for row in session.scalars(stmt).all()
    ]

