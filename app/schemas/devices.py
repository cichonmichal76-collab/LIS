from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, Field

from app.schemas.common import ApiModel


class DeviceCreateRequest(ApiModel):
    code: str
    name: str = Field(validation_alias=AliasChoices("name", "display_name"))
    manufacturer: str | None = None
    model: str | None = None
    serial_no: str | None = None
    protocol_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("protocol_code", "protocol"),
    )


class DeviceSummary(ApiModel):
    id: UUID
    code: str
    name: str
    manufacturer: str | None = None
    model: str | None = None
    serial_no: str | None = None
    protocol_code: str | None = None
    active: bool
    created_at: datetime


class DeviceTestMapCreateRequest(ApiModel):
    incoming_test_code: str
    test_catalog_id: UUID
    default_unit_ucum: str | None = None


class DeviceTestMapSummary(ApiModel):
    id: UUID
    device_id: UUID
    incoming_test_code: str
    test_catalog_id: UUID
    default_unit_ucum: str | None = None
    active: bool
    local_code: str
    display_name: str
    loinc_num: str | None = None
    created_at: datetime
