from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class OrderPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    ASAP = "asap"
    STAT = "stat"


class OrderItemCreateRequest(ApiModel):
    test_catalog_id: UUID
    requested_specimen_type_code: str | None = None
    priority: OrderPriority | None = None
    reflex_policy_code: str | None = None
    aoe_payload: dict[str, Any] = Field(default_factory=dict)


class CreateOrderRequest(ApiModel):
    patient_id: UUID
    encounter_case_id: UUID | None = None
    source_system: str
    placer_order_no: str | None = None
    priority: OrderPriority
    clinical_info: str | None = None
    requested_by_practitioner_role_id: UUID | None = None
    ordered_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    items: list[OrderItemCreateRequest]


class OrderSummary(ApiModel):
    id: UUID
    requisition_no: str
    patient_id: UUID
    source_system: str
    priority: str
    status: str
    ordered_at: datetime


class OrderItemSummary(ApiModel):
    id: UUID
    order_id: UUID
    line_no: int
    test_catalog_id: UUID
    requested_specimen_type_code: str | None = None
    status: str
    priority: str | None = None


class OrderDetail(OrderSummary):
    encounter_case_id: UUID | None = None
    clinical_info: str | None = None
    items: list[OrderItemSummary] = Field(default_factory=list)


class OrderItemActionRequest(ApiModel):
    reason: str
    comment: str | None = None

