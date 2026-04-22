from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class ReportStatus(str, Enum):
    REGISTERED = "registered"
    PARTIAL = "partial"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    ENTERED_IN_ERROR = "entered_in_error"


class CreateReportRequest(ApiModel):
    order_id: UUID
    code_local: str | None = None
    code_loinc: str | None = None
    conclusion_text: str | None = None


class AuthorizeReportRequest(ApiModel):
    signed_by_user_id: UUID


class AmendReportRequest(ApiModel):
    signed_by_user_id: UUID
    reason: str
    conclusion_text: str | None = None


class DiagnosticReportVersionSummary(ApiModel):
    id: UUID
    report_id: UUID
    version_no: int
    status: ReportStatus
    amendment_reason: str | None = None
    rendered_pdf_uri: str | None = None
    signed_by_user_id: UUID | None = None
    signed_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DiagnosticReportSummary(ApiModel):
    id: UUID
    report_no: str
    order_id: UUID
    patient_id: UUID
    status: ReportStatus
    category_code: str
    code_local: str | None = None
    code_loinc: str | None = None
    effective_at: datetime | None = None
    issued_at: datetime | None = None
    conclusion_text: str | None = None
    current_version_no: int
    versions: list[DiagnosticReportVersionSummary] = Field(default_factory=list)
    observation_ids: list[UUID] = Field(default_factory=list)

