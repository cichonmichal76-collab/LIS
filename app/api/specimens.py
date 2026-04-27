from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.specimens import (
    AccessionSpecimenRequest,
    AliquotSpecimenRequest,
    CollectSpecimenRequest,
    MoveSpecimenRequest,
    ReceiveSpecimenRequest,
    RejectSpecimenRequest,
    SpecimenSummary,
    SpecimenTraceResponse,
)
from app.services import specimens as specimen_service

router = APIRouter(prefix="/api/v1", tags=["specimens"])


@router.get("/specimens", response_model=dict[str, list[SpecimenSummary]])
def list_specimens(
    session: DbSession,
    accession_no: str | None = None,
    order_id: UUID | None = None,
    patient_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[SpecimenSummary]]:
    return {
        "items": specimen_service.list_specimens(
            session,
            accession_no=accession_no,
            order_id=order_id,
            patient_id=patient_id,
            status_filter=status_filter,
        )
    }


@router.post(
    "/specimens/accession",
    response_model=SpecimenSummary,
    status_code=status.HTTP_201_CREATED,
)
def accession_specimen(
    payload: AccessionSpecimenRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.accession_specimen(session, payload, actor=current_user)


@router.post("/specimens/{specimen_id}/collect", response_model=SpecimenSummary)
def collect_specimen(
    specimen_id: UUID,
    payload: CollectSpecimenRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.collect_specimen(session, specimen_id, payload, actor=current_user)


@router.post("/specimens/{specimen_id}/receive", response_model=SpecimenSummary)
def receive_specimen(
    specimen_id: UUID,
    payload: ReceiveSpecimenRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.receive_specimen(session, specimen_id, payload, actor=current_user)


@router.post("/specimens/{specimen_id}/accept", response_model=SpecimenSummary)
def accept_specimen(
    specimen_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.accept_specimen(session, specimen_id, actor=current_user)


@router.post("/specimens/{specimen_id}/reject", response_model=SpecimenSummary)
def reject_specimen(
    specimen_id: UUID,
    payload: RejectSpecimenRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.reject_specimen(session, specimen_id, payload, actor=current_user)


@router.post(
    "/specimens/{specimen_id}/aliquot",
    response_model=SpecimenSummary,
    status_code=status.HTTP_201_CREATED,
)
def aliquot_specimen(
    specimen_id: UUID,
    payload: AliquotSpecimenRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.aliquot_specimen(session, specimen_id, payload, actor=current_user)


@router.post("/specimens/{specimen_id}/move", response_model=SpecimenSummary)
def move_specimen(
    specimen_id: UUID,
    payload: MoveSpecimenRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER, RoleCode.TECHNICIAN)
    ),
) -> SpecimenSummary:
    return specimen_service.move_specimen(session, specimen_id, payload, actor=current_user)


@router.get("/specimens/{specimen_id}/trace", response_model=SpecimenTraceResponse)
def get_specimen_trace(
    specimen_id: UUID,
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
) -> SpecimenTraceResponse:
    return specimen_service.get_specimen_trace(session, specimen_id)
