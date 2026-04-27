from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import ContainerRecord, OrderRecord, PatientRecord, SpecimenEventRecord, SpecimenRecord
from app.schemas.auth import UserSummary
from app.schemas.specimens import (
    AccessionSpecimenRequest,
    AliquotSpecimenRequest,
    CollectSpecimenRequest,
    MoveSpecimenRequest,
    ReceiveSpecimenRequest,
    RejectSpecimenRequest,
    SpecimenSummary,
    SpecimenTraceEvent,
    SpecimenTraceResponse,
)
from app.services.audit import write_audit_event


def list_specimens(
    session: Session,
    *,
    accession_no: str | None = None,
    order_id: UUID | None = None,
    patient_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[SpecimenSummary]:
    stmt = select(SpecimenRecord).order_by(SpecimenRecord.created_at.desc())

    if accession_no:
        stmt = stmt.where(SpecimenRecord.accession_no == accession_no)
    if order_id:
        stmt = stmt.where(SpecimenRecord.order_id == str(order_id))
    if patient_id:
        stmt = stmt.where(SpecimenRecord.patient_id == str(patient_id))
    if status_filter:
        stmt = stmt.where(SpecimenRecord.status == status_filter)

    return [_to_specimen_summary(item) for item in session.scalars(stmt).all()]


def accession_specimen(
    session: Session,
    payload: AccessionSpecimenRequest,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    order = _ensure_order_exists(session, payload.order_id)
    _ensure_patient_exists(session, payload.patient_id)
    if str(payload.patient_id) != order.patient_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Specimen patient does not match the order patient.",
        )
    if payload.parent_specimen_id:
        _get_specimen_or_404(session, payload.parent_specimen_id)

    specimen = SpecimenRecord(
        id=str(uuid4()),
        accession_no=_generate_identifier("ACC"),
        order_id=str(payload.order_id),
        parent_specimen_id=_optional_uuid(payload.parent_specimen_id),
        patient_id=str(payload.patient_id),
        specimen_type_code=payload.specimen_type_code,
        status="expected",
        source_location_id=_optional_uuid(payload.source_location_id),
        notes=payload.notes,
        specimen_metadata=payload.metadata,
    )
    session.add(specimen)
    _record_specimen_event(
        session,
        specimen=specimen,
        event_type="accessioned",
        performed_by_user_id=str(actor.id) if actor else None,
        location_id=specimen.source_location_id,
        details={"parent_specimen_id": specimen.parent_specimen_id},
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=specimen.id,
        action="accession",
        status=specimen.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"order_id": specimen.order_id},
    )
    session.commit()
    session.refresh(specimen)
    return _to_specimen_summary(specimen)


def collect_specimen(
    session: Session,
    specimen_id: UUID,
    payload: CollectSpecimenRequest,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    specimen = _get_specimen_or_404(session, specimen_id)
    _require_status(specimen, allowed={"expected"}, action="collect")

    specimen.status = "collected"
    specimen.collected_at = payload.collected_at
    specimen.collected_by_practitioner_role_id = _optional_uuid(payload.collected_by_practitioner_role_id)
    if payload.container_barcodes:
        _synchronize_containers(
            session,
            specimen=specimen,
            barcodes=payload.container_barcodes,
        )
    _record_specimen_event(
        session,
        specimen=specimen,
        event_type="collected",
        performed_by_user_id=str(actor.id) if actor else None,
        details={"container_barcodes": payload.container_barcodes},
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=specimen.id,
        action="collect",
        status=specimen.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"container_count": len(payload.container_barcodes)},
    )
    session.commit()
    session.refresh(specimen)
    return _to_specimen_summary(specimen)


def receive_specimen(
    session: Session,
    specimen_id: UUID,
    payload: ReceiveSpecimenRequest,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    specimen = _get_specimen_or_404(session, specimen_id)
    _require_status(specimen, allowed={"expected", "collected"}, action="receive")

    specimen.status = "received"
    specimen.received_at = payload.received_at
    specimen.storage_location_id = _optional_uuid(payload.location_id)
    _record_specimen_event(
        session,
        specimen=specimen,
        event_type="received",
        performed_by_user_id=str(actor.id) if actor else None,
        location_id=specimen.storage_location_id,
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=specimen.id,
        action="receive",
        status=specimen.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"location_id": specimen.storage_location_id},
    )
    session.commit()
    session.refresh(specimen)
    return _to_specimen_summary(specimen)


def accept_specimen(
    session: Session,
    specimen_id: UUID,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    specimen = _get_specimen_or_404(session, specimen_id)
    _require_status(specimen, allowed={"received"}, action="accept")

    specimen.status = "accepted"
    specimen.accepted_at = datetime.now(UTC)
    _record_specimen_event(
        session,
        specimen=specimen,
        event_type="accepted",
        performed_by_user_id=str(actor.id) if actor else None,
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=specimen.id,
        action="accept",
        status=specimen.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
    )
    session.commit()
    session.refresh(specimen)
    return _to_specimen_summary(specimen)


def reject_specimen(
    session: Session,
    specimen_id: UUID,
    payload: RejectSpecimenRequest,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    specimen = _get_specimen_or_404(session, specimen_id)
    if specimen.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Specimen is already rejected.",
        )

    specimen.status = "rejected"
    specimen.rejected_at = datetime.now(UTC)
    specimen.rejection_reason_code = payload.rejection_reason_code
    if payload.notes:
        specimen.notes = payload.notes
    _record_specimen_event(
        session,
        specimen=specimen,
        event_type="rejected",
        performed_by_user_id=str(actor.id) if actor else None,
        details={"rejection_reason_code": payload.rejection_reason_code, "notes": payload.notes},
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=specimen.id,
        action="reject",
        status=specimen.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"rejection_reason_code": payload.rejection_reason_code},
    )
    session.commit()
    session.refresh(specimen)
    return _to_specimen_summary(specimen)


def aliquot_specimen(
    session: Session,
    specimen_id: UUID,
    payload: AliquotSpecimenRequest,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    parent = _get_specimen_or_404(session, specimen_id)
    if parent.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rejected specimens cannot be aliquoted.",
        )

    child = SpecimenRecord(
        id=str(uuid4()),
        accession_no=_generate_identifier("ALQ"),
        order_id=parent.order_id,
        parent_specimen_id=parent.id,
        patient_id=parent.patient_id,
        specimen_type_code=parent.specimen_type_code,
        status=_derive_child_status(parent.status),
        collected_at=parent.collected_at,
        received_at=parent.received_at,
        accepted_at=parent.accepted_at,
        source_location_id=parent.source_location_id,
        storage_location_id=parent.storage_location_id,
        notes=payload.notes,
        specimen_metadata={
            "container_type_code": payload.container_type_code,
            "barcode": payload.barcode,
            "volume_value": payload.volume_value,
            "volume_ucum": payload.volume_ucum,
        },
    )
    session.add(child)
    if payload.barcode:
        session.add(
            ContainerRecord(
                id=str(uuid4()),
                specimen=child,
                barcode=payload.barcode,
                container_type_code=payload.container_type_code or "tube",
                volume_value=payload.volume_value,
                volume_ucum=payload.volume_ucum,
                status="labeled",
            )
        )
    _record_specimen_event(
        session,
        specimen=parent,
        event_type="aliquoted",
        performed_by_user_id=str(actor.id) if actor else None,
        details={"child_specimen_id": child.id},
    )
    _record_specimen_event(
        session,
        specimen=child,
        event_type="aliquot-created",
        performed_by_user_id=str(actor.id) if actor else None,
        details={"parent_specimen_id": parent.id},
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=parent.id,
        action="aliquot-parent",
        status=parent.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"child_specimen_id": child.id},
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=child.id,
        action="aliquot-create",
        status=child.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"parent_specimen_id": parent.id},
    )
    session.commit()
    session.refresh(child)
    return _to_specimen_summary(child)


def move_specimen(
    session: Session,
    specimen_id: UUID,
    payload: MoveSpecimenRequest,
    *,
    actor: UserSummary | None = None,
) -> SpecimenSummary:
    specimen = _get_specimen_or_404(session, specimen_id)
    specimen.storage_location_id = str(payload.storage_location_id)
    specimen.position_code = payload.position_code
    _record_specimen_event(
        session,
        specimen=specimen,
        event_type="moved",
        performed_by_user_id=str(actor.id) if actor else None,
        location_id=specimen.storage_location_id,
        details={"position_code": payload.position_code, "comment": payload.comment},
    )
    write_audit_event(
        session,
        entity_type="specimen",
        entity_id=specimen.id,
        action="move",
        status=specimen.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"storage_location_id": specimen.storage_location_id},
    )
    session.commit()
    session.refresh(specimen)
    return _to_specimen_summary(specimen)


def get_specimen_trace(session: Session, specimen_id: UUID) -> SpecimenTraceResponse:
    specimen = _get_specimen_or_404(session, specimen_id, with_events=True)
    return SpecimenTraceResponse(
        specimen=_to_specimen_summary(specimen),
        events=[
            SpecimenTraceEvent(
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                performed_by_user_id=event.performed_by_user_id,
                location_id=event.location_id,
                details=event.details,
            )
            for event in specimen.events
        ],
    )


def _ensure_order_exists(session: Session, order_id: UUID) -> OrderRecord:
    order = session.get(OrderRecord, str(order_id))
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} was not found.",
        )
    return order


def _ensure_patient_exists(session: Session, patient_id: UUID) -> None:
    patient = session.get(PatientRecord, str(patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} was not found.",
        )


def _get_specimen_or_404(
    session: Session,
    specimen_id: UUID,
    *,
    with_events: bool = False,
) -> SpecimenRecord:
    stmt = select(SpecimenRecord).where(SpecimenRecord.id == str(specimen_id))
    if with_events:
        stmt = stmt.options(selectinload(SpecimenRecord.events))
    specimen = session.scalar(stmt)
    if specimen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specimen {specimen_id} was not found.",
        )
    return specimen


def _record_specimen_event(
    session: Session,
    *,
    specimen: SpecimenRecord,
    event_type: str,
    performed_by_user_id: str | None = None,
    location_id: str | None = None,
    details: dict[str, object] | None = None,
    ) -> None:
    session.add(
        SpecimenEventRecord(
            id=str(uuid4()),
            specimen=specimen,
            event_type=event_type,
            performed_by_user_id=performed_by_user_id,
            location_id=location_id,
            details=details or {},
        )
    )


def _synchronize_containers(
    session: Session,
    *,
    specimen: SpecimenRecord,
    barcodes: list[str],
) -> None:
    existing_barcodes = {container.barcode for container in specimen.containers}
    next_position = len(specimen.containers) + 1
    for barcode in barcodes:
        normalized = barcode.strip()
        if not normalized or normalized in existing_barcodes:
            continue
        session.add(
            ContainerRecord(
                id=str(uuid4()),
                specimen=specimen,
                barcode=normalized,
                container_type_code="tube",
                position_code=str(next_position),
                status="labeled",
            )
        )
        existing_barcodes.add(normalized)
        next_position += 1


def _require_status(specimen: SpecimenRecord, *, allowed: set[str], action: str) -> None:
    if specimen.status not in allowed:
        allowed_display = ", ".join(sorted(allowed))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot {action} specimen while it is in status '{specimen.status}'. "
                f"Allowed statuses: {allowed_display}."
            ),
        )


def _derive_child_status(parent_status: str) -> str:
    if parent_status in {"accepted", "received", "collected"}:
        return parent_status
    return "expected"


def _generate_identifier(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"


def _optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None


def _to_specimen_summary(specimen: SpecimenRecord) -> SpecimenSummary:
    return SpecimenSummary(
        id=specimen.id,
        accession_no=specimen.accession_no,
        order_id=specimen.order_id,
        patient_id=specimen.patient_id,
        specimen_type_code=specimen.specimen_type_code,
        status=specimen.status,
        collected_at=specimen.collected_at,
        received_at=specimen.received_at,
    )
