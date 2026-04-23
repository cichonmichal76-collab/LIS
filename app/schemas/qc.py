from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class QcDecision(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class QcRunStatus(str, Enum):
    OPEN = "open"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class QcRuleType(str, Enum):
    RANGE = "range"
    WESTGARD_12S = "westgard_12s"
    WESTGARD_13S = "westgard_13s"
    WESTGARD_22S = "westgard_22s"
    WESTGARD_R4S = "westgard_r4s"
    WESTGARD_41S = "westgard_41s"


class QcMaterialCreateRequest(ApiModel):
    code: str
    name: str
    manufacturer: str | None = None
    active: bool = True


class QcMaterialSummary(ApiModel):
    id: UUID
    code: str
    name: str
    manufacturer: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime


class QcLotCreateRequest(ApiModel):
    material_id: UUID
    lot_no: str
    test_catalog_id: UUID
    device_id: UUID | None = None
    unit_ucum: str | None = None
    target_mean: float | None = None
    target_sd: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    active: bool = True
    expires_at: datetime | None = None


class QcLotSummary(ApiModel):
    id: UUID
    material_id: UUID
    lot_no: str
    test_catalog_id: UUID
    device_id: UUID | None = None
    unit_ucum: str | None = None
    target_mean: float | None = None
    target_sd: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    active: bool
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class QcRuleCreateRequest(ApiModel):
    name: str
    active: bool = True
    priority: int = 100
    test_catalog_id: UUID | None = None
    device_id: UUID | None = None
    rule_type: QcRuleType = QcRuleType.RANGE
    params: dict[str, Any] = Field(default_factory=dict)


class QcRuleSummary(ApiModel):
    id: UUID
    name: str
    active: bool
    priority: int
    test_catalog_id: UUID | None = None
    device_id: UUID | None = None
    rule_type: QcRuleType
    params: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class QcRunCreateRequest(ApiModel):
    lot_id: UUID
    device_id: UUID | None = None
    started_at: datetime | None = None


class QcResultCreateRequest(ApiModel):
    test_catalog_id: UUID
    value_num: float
    unit_ucum: str | None = None
    observed_at: datetime | None = None
    raw_message_id: UUID | None = None


class QcResultSummary(ApiModel):
    id: UUID
    run_id: UUID
    test_catalog_id: UUID
    value_num: float
    unit_ucum: str | None = None
    decision: QcDecision | None = None
    z_score: float | None = None
    warning_rules: list[str] = Field(default_factory=list)
    failure_rules: list[str] = Field(default_factory=list)
    observed_at: datetime | None = None
    evaluated_at: datetime | None = None
    raw_message_id: UUID | None = None
    created_at: datetime


class QcRunSummary(ApiModel):
    id: UUID
    lot_id: UUID
    device_id: UUID | None = None
    status: QcRunStatus
    started_at: datetime
    evaluated_at: datetime | None = None
    reviewed_by_user_id: UUID | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class QcRunEvaluationResponse(ApiModel):
    run: QcRunSummary
    results: list[QcResultSummary] = Field(default_factory=list)


class QcGateDecision(ApiModel):
    applies: bool
    allowed: bool
    reasons: list[str] = Field(default_factory=list)
    latest_run_id: UUID | None = None
    latest_result_id: UUID | None = None
    latest_decision: QcDecision | None = None
