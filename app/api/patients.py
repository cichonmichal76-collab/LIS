from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.patients import PatientCreateRequest, PatientSummary
from app.services import patients as patient_service

router = APIRouter(prefix="/api/v1", tags=["patients"])


@router.post("/patients", response_model=PatientSummary, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER)),
) -> PatientSummary:
    return patient_service.create_patient(session, payload, actor=current_user)


@router.get("/patients", response_model=dict[str, list[PatientSummary]])
def list_patients(
    session: DbSession,
    mrn: str | None = Query(default=None),
    family_name: str | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[PatientSummary]]:
    return {
        "items": patient_service.list_patients(
            session,
            mrn=mrn,
            family_name=family_name,
        )
    }


@router.get("/patients/{patient_id}", response_model=PatientSummary)
def get_patient(
    patient_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> PatientSummary:
    return patient_service.get_patient(session, patient_id)
