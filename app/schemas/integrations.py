from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from app.schemas.autoverification import AutoverificationApplyResponse
from app.schemas.common import ApiModel
from app.schemas.observations import ObservationSummary, ObservationValueType
from app.schemas.orders import OrderItemSummary, OrderSummary
from app.schemas.patients import PatientSummary
from app.schemas.specimens import SpecimenSummary


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ASTMMessageImportRequest(ApiModel):
    device_id: UUID
    message: str
    auto_verify: bool = False


class HL7MessageImportRequest(ApiModel):
    message: str
    create_missing_patient: bool = True


class InterfaceMessageSummary(ApiModel):
    id: UUID
    protocol: str
    direction: MessageDirection
    message_type: str
    control_id: str | None = None
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    processed_ok: bool
    error_text: str | None = None
    created_at: datetime


class RawInstrumentMessageSummary(ApiModel):
    id: UUID
    device_id: UUID
    protocol: str
    direction: MessageDirection
    message_type: str | None = None
    accession_no: str | None = None
    specimen_barcode: str | None = None
    parser_version: str
    parsed_ok: bool
    parse_error: str | None = None
    created_observation_count: int
    created_at: datetime


class DeviceWorklistItem(ApiModel):
    order_item_id: UUID
    order_id: UUID
    requisition_no: str
    specimen_id: UUID
    accession_no: str
    specimen_barcode: str | None = None
    incoming_test_code: str
    test_catalog_id: UUID
    local_code: str
    display_name: str
    loinc_num: str | None = None
    order_item_status: str
    specimen_status: str


class DeviceWorklistResponse(ApiModel):
    device_id: UUID
    items: list[DeviceWorklistItem] = Field(default_factory=list)


class DeviceResultEntryRequest(ApiModel):
    incoming_test_code: str
    value_type: ObservationValueType
    value_num: float | None = None
    value_text: str | None = None
    value_boolean: bool | None = None
    value_code_system: str | None = None
    value_code: str | None = None
    unit_ucum: str | None = None
    abnormal_flag: str | None = None
    effective_at: datetime | None = None


class DeviceGatewayIngestRequest(ApiModel):
    device_id: UUID
    protocol: str = "device-gateway"
    accession_no: str | None = None
    specimen_barcode: str | None = None
    auto_verify: bool = False
    results: list[DeviceResultEntryRequest]


class IntegratedObservationSummary(ObservationSummary):
    autoverification: AutoverificationApplyResponse | None = None


class DeviceGatewayIngestResponse(ApiModel):
    raw_message_id: UUID
    device_id: UUID
    order_id: UUID
    specimen_id: UUID
    created_observations: list[IntegratedObservationSummary] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ASTMImportResponse(ApiModel):
    raw_message_id: UUID
    device_id: UUID
    created_observations: list[IntegratedObservationSummary] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class HL7OrderImportResponse(ApiModel):
    message_log_id: UUID
    patient: PatientSummary
    order: OrderSummary
    items: list[OrderItemSummary] = Field(default_factory=list)
    specimens: list[SpecimenSummary] = Field(default_factory=list)


class HL7ResultImportResponse(ApiModel):
    message_log_id: UUID
    order_id: UUID
    specimen_id: UUID | None = None
    created_observation_ids: list[UUID] = Field(default_factory=list)
    observations: list[ObservationSummary] = Field(default_factory=list)
