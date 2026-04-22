from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from app.schemas.common import ApiModel


class TestCatalogKind(str, Enum):
    ORDERABLE = "orderable"
    PANEL = "panel"
    ANALYTE = "analyte"
    AOE = "aoe"


class ResultValueType(str, Enum):
    QUANTITY = "quantity"
    TEXT = "text"
    CODED = "coded"
    BOOLEAN = "boolean"
    RANGE = "range"
    ATTACHMENT = "attachment"


class TestCatalogCreateRequest(ApiModel):
    local_code: str
    display_name: str
    kind: TestCatalogKind = TestCatalogKind.ORDERABLE
    loinc_num: str | None = None
    specimen_type_code: str | None = None
    default_ucum: str | None = None
    result_value_type: ResultValueType = ResultValueType.QUANTITY


class TestCatalogSummary(ApiModel):
    id: UUID
    local_code: str
    display_name: str
    kind: TestCatalogKind
    loinc_num: str | None = None
    specimen_type_code: str | None = None
    default_ucum: str | None = None
    result_value_type: ResultValueType
    active: bool
    created_at: datetime
