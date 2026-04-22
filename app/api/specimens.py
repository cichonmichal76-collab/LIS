from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.helpers import raise_not_implemented
from app.schemas.common import ApiError
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

router = APIRouter(prefix="/api/v1", tags=["specimens"])
NOT_IMPLEMENTED = {
    status.HTTP_501_NOT_IMPLEMENTED: {
        "model": ApiError,
        "description": "Route exists, but workflow logic is not implemented yet.",
    }
}


@router.post(
    "/specimens/accession",
    response_model=SpecimenSummary,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_IMPLEMENTED,
)
def accession_specimen(payload: AccessionSpecimenRequest) -> SpecimenSummary:
    del payload
    raise_not_implemented("Specimen accessioning")


@router.post("/specimens/{specimen_id}/collect", response_model=SpecimenSummary, responses=NOT_IMPLEMENTED)
def collect_specimen(specimen_id: UUID, payload: CollectSpecimenRequest) -> SpecimenSummary:
    del specimen_id, payload
    raise_not_implemented("Specimen collection")


@router.post("/specimens/{specimen_id}/receive", response_model=SpecimenSummary, responses=NOT_IMPLEMENTED)
def receive_specimen(specimen_id: UUID, payload: ReceiveSpecimenRequest) -> SpecimenSummary:
    del specimen_id, payload
    raise_not_implemented("Specimen receiving")


@router.post("/specimens/{specimen_id}/accept", response_model=SpecimenSummary, responses=NOT_IMPLEMENTED)
def accept_specimen(specimen_id: UUID) -> SpecimenSummary:
    del specimen_id
    raise_not_implemented("Specimen acceptance")


@router.post("/specimens/{specimen_id}/reject", response_model=SpecimenSummary, responses=NOT_IMPLEMENTED)
def reject_specimen(specimen_id: UUID, payload: RejectSpecimenRequest) -> SpecimenSummary:
    del specimen_id, payload
    raise_not_implemented("Specimen rejection")


@router.post(
    "/specimens/{specimen_id}/aliquot",
    response_model=SpecimenSummary,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_IMPLEMENTED,
)
def aliquot_specimen(specimen_id: UUID, payload: AliquotSpecimenRequest) -> SpecimenSummary:
    del specimen_id, payload
    raise_not_implemented("Specimen aliquoting")


@router.post("/specimens/{specimen_id}/move", response_model=SpecimenSummary, responses=NOT_IMPLEMENTED)
def move_specimen(specimen_id: UUID, payload: MoveSpecimenRequest) -> SpecimenSummary:
    del specimen_id, payload
    raise_not_implemented("Specimen movement")


@router.get("/specimens/{specimen_id}/trace", response_model=SpecimenTraceResponse, responses=NOT_IMPLEMENTED)
def get_specimen_trace(specimen_id: UUID) -> SpecimenTraceResponse:
    del specimen_id
    raise_not_implemented("Specimen trace")

