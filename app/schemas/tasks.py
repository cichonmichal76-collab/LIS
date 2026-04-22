from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class TaskFocusType(str, Enum):
    ORDER_ITEM = "order-item"
    SPECIMEN = "specimen"
    OBSERVATION = "observation"
    REPORT = "report"


class CreateTaskRequest(ApiModel):
    group_identifier: str | None = None
    based_on_order_item_id: UUID | None = None
    focus_type: TaskFocusType
    focus_id: UUID
    queue_code: str
    status: str
    business_status: str | None = None
    priority: str | None = None
    owner_user_id: UUID | None = None
    owner_practitioner_role_id: UUID | None = None
    device_id: UUID | None = None
    due_at: datetime | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)


class TaskActionRequest(ApiModel):
    owner_user_id: UUID | None = None
    owner_practitioner_role_id: UUID | None = None
    business_status: str | None = None
    reason: str | None = None
    comment: str | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)


class TaskSummary(ApiModel):
    id: UUID
    group_identifier: str | None = None
    based_on_order_item_id: UUID | None = None
    focus_type: TaskFocusType
    focus_id: UUID
    queue_code: str
    status: str
    business_status: str | None = None
    priority: str | None = None
    owner_user_id: UUID | None = None
    authored_on: datetime
    due_at: datetime | None = None

