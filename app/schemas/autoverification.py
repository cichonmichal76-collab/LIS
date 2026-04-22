from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class AutoverificationRuleType(str, Enum):
    BASIC = "basic"
    DELTA = "delta"


class AutoverificationCheckDecision(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class AutoverificationApplyDecision(str, Enum):
    AUTO_FINALIZED = "auto_finalized"
    HELD = "held"


class AutoverificationRuleCreateRequest(ApiModel):
    name: str
    active: bool = True
    priority: int = 100
    test_catalog_id: UUID | None = None
    device_id: UUID | None = None
    specimen_type_code: str | None = None
    rule_type: AutoverificationRuleType = AutoverificationRuleType.BASIC
    condition: dict[str, Any] = Field(default_factory=dict)


class AutoverificationRuleSummary(ApiModel):
    id: UUID
    name: str
    active: bool
    priority: int
    test_catalog_id: UUID | None = None
    device_id: UUID | None = None
    specimen_type_code: str | None = None
    rule_type: AutoverificationRuleType
    condition: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class AutoverificationRuleEvaluation(ApiModel):
    rule_id: UUID
    rule_name: str
    priority: int
    decision: AutoverificationCheckDecision
    reasons: list[str] = Field(default_factory=list)
    condition: dict[str, Any] = Field(default_factory=dict)


class AutoverificationEvaluateResponse(ApiModel):
    observation_id: UUID
    previous_final_observation_id: UUID | None = None
    overall_decision: AutoverificationCheckDecision
    matched_rule_count: int
    implicit_reasons: list[str] = Field(default_factory=list)
    rules: list[AutoverificationRuleEvaluation] = Field(default_factory=list)


class AutoverificationApplyResponse(ApiModel):
    observation_id: UUID
    decision: AutoverificationApplyDecision
    matched_rule_count: int
    reasons: list[str] = Field(default_factory=list)
    created_task_id: UUID | None = None
    rules: list[AutoverificationRuleEvaluation] = Field(default_factory=list)


class AutoverificationRunSummary(ApiModel):
    id: UUID
    observation_id: UUID
    rule_id: UUID | None = None
    decision: str
    reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime
    created_task_id: UUID | None = None
