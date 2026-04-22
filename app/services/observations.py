from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import ObservationLinkRecord, ObservationRecord, OrderItemRecord, SpecimenRecord
from app.schemas.observations import (
    CorrectObservationRequest,
    CreateManualObservationRequest,
    ObservationSummary,
    TechnicalVerifyObservationRequest,
)
from app.services.audit import write_audit_event
from app.services.provenance import write_provenance_record


def create_manual_observation(
    session: Session,
    payload: CreateManualObservationRequest,
    *,
    actor_user_id: str | None = None,
) -> ObservationSummary:
    order_item = _get_order_item_or_404(session, payload.order_item_id)
    specimen_id = _validate_specimen_for_order_item(session, payload.specimen_id, order_item.order_id)

    observation = ObservationRecord(
        id=str(uuid4()),
        order_item_id=order_item.id,
        specimen_id=specimen_id,
        code_local=payload.code_local,
        code_loinc=payload.code_loinc,
        status=payload.status.value,
        category_code="laboratory",
        value_type=payload.value_type.value,
        value_num=payload.value_num,
        value_text=payload.value_text,
        value_boolean=payload.value_boolean,
        value_code_system=payload.value_code_system,
        value_code=payload.value_code,
        unit_ucum=payload.unit_ucum,
        interpretation_code=payload.interpretation_code,
        abnormal_flag=payload.abnormal_flag,
        method_code=payload.method_code,
        device_id=_optional_uuid(payload.device_id),
        effective_at=payload.effective_at,
        issued_at=None,
        reference_interval_snapshot=payload.reference_interval_snapshot,
    )
    session.add(observation)
    write_audit_event(
        session,
        entity_type="observation",
        entity_id=observation.id,
        action="create",
        status=observation.status,
        context={"actor_user_id": actor_user_id, "order_item_id": observation.order_item_id},
    )
    write_provenance_record(
        session,
        target_resource_type="observation",
        target_resource_id=observation.id,
        activity_code="observation-created",
        based_on_order_item_id=observation.order_item_id,
        specimen_id=observation.specimen_id,
        observation_id=observation.id,
        agent_user_id=actor_user_id,
        inputs=payload.model_dump(mode="json"),
    )
    session.commit()
    session.refresh(observation)
    return _to_observation_summary(observation)


def list_observations(
    session: Session,
    *,
    specimen_id: UUID | None = None,
    order_item_id: UUID | None = None,
) -> list[ObservationSummary]:
    stmt: Select[tuple[ObservationRecord]] = select(ObservationRecord).order_by(
        ObservationRecord.created_at.desc()
    )
    if specimen_id:
        stmt = stmt.where(ObservationRecord.specimen_id == str(specimen_id))
    if order_item_id:
        stmt = stmt.where(ObservationRecord.order_item_id == str(order_item_id))
    return [_to_observation_summary(row) for row in session.scalars(stmt).all()]


def get_observation(session: Session, observation_id: UUID) -> ObservationSummary:
    observation = _get_observation_or_404(session, observation_id)
    return _to_observation_summary(observation)


def technical_verify_observation(
    session: Session,
    observation_id: UUID,
    payload: TechnicalVerifyObservationRequest,
    *,
    actor_user_id: str | None = None,
) -> ObservationSummary:
    observation = _get_observation_or_404(session, observation_id)
    if observation.status not in {"registered", "preliminary"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Observation {observation_id} cannot be technically verified from status '{observation.status}'.",
        )

    observation.status = "final"
    observation.issued_at = datetime.now(UTC)
    write_audit_event(
        session,
        entity_type="observation",
        entity_id=observation.id,
        action="technical-verify",
        status=observation.status,
        context={"actor_user_id": actor_user_id, "notes": payload.notes},
    )
    write_provenance_record(
        session,
        target_resource_type="observation",
        target_resource_id=observation.id,
        activity_code="observation-verified",
        based_on_order_item_id=observation.order_item_id,
        specimen_id=observation.specimen_id,
        observation_id=observation.id,
        agent_user_id=actor_user_id,
        inputs={"notes": payload.notes, "status": observation.status},
    )
    session.commit()
    session.refresh(observation)
    return _to_observation_summary(observation)


def correct_observation(
    session: Session,
    observation_id: UUID,
    payload: CorrectObservationRequest,
    *,
    actor_user_id: str | None = None,
) -> ObservationSummary:
    original = _get_observation_or_404(session, observation_id)
    if original.status in {"cancelled", "entered_in_error"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Observation {observation_id} cannot be corrected from status '{original.status}'.",
        )

    original.status = "corrected"
    write_audit_event(
        session,
        entity_type="observation",
        entity_id=original.id,
        action="mark-corrected",
        status=original.status,
        context={"actor_user_id": actor_user_id, "reason": payload.reason},
    )
    write_provenance_record(
        session,
        target_resource_type="observation",
        target_resource_id=original.id,
        activity_code="observation-corrected",
        based_on_order_item_id=original.order_item_id,
        specimen_id=original.specimen_id,
        observation_id=original.id,
        agent_user_id=actor_user_id,
        inputs={"reason": payload.reason},
    )

    replacement_summary = _to_observation_summary(original)
    if payload.replacement is not None:
        replacement_payload = payload.replacement.model_copy(
            update={
                "order_item_id": payload.replacement.order_item_id or UUID(original.order_item_id),
                "specimen_id": payload.replacement.specimen_id or _uuid_or_none(original.specimen_id),
            }
        )
        replacement = ObservationRecord(
            id=str(uuid4()),
            order_item_id=str(replacement_payload.order_item_id),
            specimen_id=_optional_uuid(replacement_payload.specimen_id),
            code_local=replacement_payload.code_local,
            code_loinc=replacement_payload.code_loinc,
            status=replacement_payload.status.value,
            category_code="laboratory",
            value_type=replacement_payload.value_type.value,
            value_num=replacement_payload.value_num,
            value_text=replacement_payload.value_text,
            value_boolean=replacement_payload.value_boolean,
            value_code_system=replacement_payload.value_code_system,
            value_code=replacement_payload.value_code,
            unit_ucum=replacement_payload.unit_ucum,
            interpretation_code=replacement_payload.interpretation_code,
            abnormal_flag=replacement_payload.abnormal_flag,
            method_code=replacement_payload.method_code,
            device_id=_optional_uuid(replacement_payload.device_id),
            effective_at=replacement_payload.effective_at,
            reference_interval_snapshot=replacement_payload.reference_interval_snapshot,
        )
        session.add(replacement)
        session.add(
            ObservationLinkRecord(
                id=str(uuid4()),
                source_observation_id=replacement.id,
                target_observation_id=original.id,
                relation_type="replaces",
            )
        )
        write_audit_event(
            session,
            entity_type="observation",
            entity_id=replacement.id,
            action="replacement-create",
            status=replacement.status,
            context={"actor_user_id": actor_user_id, "replaces": original.id},
        )
        write_provenance_record(
            session,
            target_resource_type="observation",
            target_resource_id=replacement.id,
            activity_code="observation-replacement-created",
            based_on_order_item_id=replacement.order_item_id,
            specimen_id=replacement.specimen_id,
            observation_id=replacement.id,
            agent_user_id=actor_user_id,
            inputs={"reason": payload.reason, "replaces": original.id},
        )
        session.commit()
        session.refresh(replacement)
        replacement_summary = _to_observation_summary(replacement)
        return replacement_summary

    session.commit()
    session.refresh(original)
    return replacement_summary


def _get_order_item_or_404(session: Session, order_item_id: UUID) -> OrderItemRecord:
    order_item = session.get(OrderItemRecord, str(order_item_id))
    if order_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item {order_item_id} was not found.",
        )
    return order_item


def _get_observation_or_404(session: Session, observation_id: UUID) -> ObservationRecord:
    observation = session.get(ObservationRecord, str(observation_id))
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation {observation_id} was not found.",
        )
    return observation


def _validate_specimen_for_order_item(
    session: Session,
    specimen_id: UUID | None,
    order_id: str,
) -> str | None:
    if specimen_id is None:
        return None
    specimen = session.get(SpecimenRecord, str(specimen_id))
    if specimen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specimen {specimen_id} was not found.",
        )
    if specimen.order_id != order_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Specimen does not belong to the same order as the observation order item.",
        )
    return specimen.id


def _optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None


def _uuid_or_none(value: str | None) -> UUID | None:
    return UUID(value) if value else None


def _to_observation_summary(observation: ObservationRecord) -> ObservationSummary:
    return ObservationSummary(
        id=observation.id,
        order_item_id=observation.order_item_id,
        specimen_id=observation.specimen_id,
        raw_message_id=observation.raw_message_id,
        code_local=observation.code_local,
        code_loinc=observation.code_loinc,
        status=observation.status,
        category_code=observation.category_code,
        value_type=observation.value_type,
        value_num=observation.value_num,
        value_text=observation.value_text,
        value_boolean=observation.value_boolean,
        value_code_system=observation.value_code_system,
        value_code=observation.value_code,
        unit_ucum=observation.unit_ucum,
        interpretation_code=observation.interpretation_code,
        abnormal_flag=observation.abnormal_flag,
        method_code=observation.method_code,
        device_id=observation.device_id,
        effective_at=observation.effective_at,
        issued_at=observation.issued_at,
        reference_interval_snapshot=observation.reference_interval_snapshot,
    )
