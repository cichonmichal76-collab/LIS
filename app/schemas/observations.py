from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class ObservationStatus(str, Enum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered_in_error"


class ObservationValueType(str, Enum):
    QUANTITY = "quantity"
    TEXT = "text"
    CODED = "coded"
    BOOLEAN = "boolean"
    RANGE = "range"
    ATTACHMENT = "attachment"


class CreateManualObservationRequest(ApiModel):
    order_item_id: UUID
    specimen_id: UUID | None = None
    code_local: str
    code_loinc: str | None = None
    status: ObservationStatus = ObservationStatus.PRELIMINARY
    value_type: ObservationValueType
    value_num: float | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_code_system: str | None = None
    value_code: str | None = None
    unit_ucum: str | None = None
    interpretation_code: str | None = None
    abnormal_flag: str | None = None
    method_code: str | None = None
    device_id: UUID | None = None
    effective_at: datetime | None = None
    reference_interval_snapshot: dict[str, Any] = Field(default_factory=dict)


class TechnicalVerifyObservationRequest(ApiModel):
    notes: str | None = None


class CorrectObservationRequest(ApiModel):
    reason: str
    replacement: CreateManualObservationRequest | None = None


class ObservationSummary(ApiModel):
    id: UUID
    order_item_id: UUID
    specimen_id: UUID | None = None
    raw_message_id: UUID | None = None
    code_local: str
    code_loinc: str | None = None
    status: ObservationStatus
    category_code: str
    value_type: ObservationValueType
    value_num: float | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_code_system: str | None = None
    value_code: str | None = None
    unit_ucum: str | None = None
    interpretation_code: str | None = None
    abnormal_flag: str | None = None
    method_code: str | None = None
    device_id: UUID | None = None
    effective_at: datetime | None = None
    issued_at: datetime | None = None
    reference_interval_snapshot: dict[str, Any] = Field(default_factory=dict)
