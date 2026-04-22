from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class AuditEventSummary(ApiModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    status: str
    source_system: str | None = None
    event_at: datetime
    context: dict[str, Any] = Field(default_factory=dict)


class ProvenanceRecordSummary(ApiModel):
    id: UUID
    target_resource_type: str
    target_resource_id: UUID
    activity_code: str
    based_on_order_id: UUID | None = None
    based_on_order_item_id: UUID | None = None
    specimen_id: UUID | None = None
    observation_id: UUID | None = None
    report_version_id: UUID | None = None
    device_id: UUID | None = None
    agent_user_id: UUID | None = None
    agent_practitioner_role_id: UUID | None = None
    recorded_at: datetime
    inputs: dict[str, Any] = Field(default_factory=dict)
    signature: dict[str, Any] = Field(default_factory=dict)
