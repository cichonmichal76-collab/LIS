from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import PatientRecord
from app.schemas.auth import UserSummary
from app.schemas.patients import PatientCreateRequest, PatientSummary
from app.services.audit import write_audit_event


def create_patient(
    session: Session,
    payload: PatientCreateRequest,
    *,
    actor: UserSummary,
) -> PatientSummary:
    existing = session.scalar(select(PatientRecord).where(PatientRecord.mrn == payload.mrn))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient MRN '{payload.mrn}' already exists.",
        )

    patient = PatientRecord(
        id=str(uuid4()),
        mrn=payload.mrn,
        given_name=payload.given_name,
        family_name=payload.family_name,
        sex_code=payload.sex_code,
        birth_date=payload.birth_date,
    )
    session.add(patient)
    write_audit_event(
        session,
        entity_type="patient",
        entity_id=patient.id,
        action="create",
        status="active",
        actor_user_id=str(actor.id),
        actor_username=actor.username,
        actor_role_code=actor.role_code.value,
        context={"mrn": patient.mrn},
    )
    session.commit()
    session.refresh(patient)
    return _to_patient_summary(patient)


def list_patients(
    session: Session,
    *,
    mrn: str | None = None,
    family_name: str | None = None,
) -> list[PatientSummary]:
    stmt: Select[tuple[PatientRecord]] = select(PatientRecord).order_by(PatientRecord.created_at.desc())
    if mrn:
        stmt = stmt.where(PatientRecord.mrn == mrn)
    if family_name:
        stmt = stmt.where(PatientRecord.family_name.ilike(f"%{family_name}%"))
    return [_to_patient_summary(patient) for patient in session.scalars(stmt).all()]


def get_patient(session: Session, patient_id: UUID) -> PatientSummary:
    patient = session.get(PatientRecord, str(patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} was not found.",
        )
    return _to_patient_summary(patient)


def _to_patient_summary(patient: PatientRecord) -> PatientSummary:
    return PatientSummary(
        id=patient.id,
        mrn=patient.mrn,
        given_name=patient.given_name,
        family_name=patient.family_name,
        sex_code=patient.sex_code,
        birth_date=patient.birth_date,
        created_at=patient.created_at,
    )
