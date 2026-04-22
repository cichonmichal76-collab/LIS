from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class AccessionSpecimenRequest(ApiModel):
    order_id: UUID
    patient_id: UUID
    parent_specimen_id: UUID | None = None
    specimen_type_code: str
    source_location_id: UUID | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectSpecimenRequest(ApiModel):
    collected_at: datetime
    collected_by_practitioner_role_id: UUID | None = None
    container_barcodes: list[str] = Field(default_factory=list)


class ReceiveSpecimenRequest(ApiModel):
    received_at: datetime
    location_id: UUID | None = None


class RejectSpecimenRequest(ApiModel):
    rejection_reason_code: str
    notes: str | None = None


class AliquotSpecimenRequest(ApiModel):
    container_type_code: str
    barcode: str | None = None
    volume_value: float | None = None
    volume_ucum: str | None = None
    notes: str | None = None


class MoveSpecimenRequest(ApiModel):
    storage_location_id: UUID
    position_code: str | None = None
    comment: str | None = None


class SpecimenSummary(ApiModel):
    id: UUID
    accession_no: str
    order_id: UUID
    patient_id: UUID
    specimen_type_code: str
    status: str
    collected_at: datetime | None = None
    received_at: datetime | None = None


class SpecimenTraceEvent(ApiModel):
    event_type: str
    occurred_at: datetime
    performed_by_user_id: UUID | None = None
    location_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class SpecimenTraceResponse(ApiModel):
    specimen: SpecimenSummary
    events: list[SpecimenTraceEvent] = Field(default_factory=list)

