from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from app.schemas.common import ApiModel


class PatientCreateRequest(ApiModel):
    mrn: str
    given_name: str
    family_name: str
    sex_code: str | None = None
    birth_date: date | None = None


class PatientSummary(ApiModel):
    id: UUID
    mrn: str
    given_name: str
    family_name: str
    sex_code: str | None = None
    birth_date: date | None = None
    created_at: datetime
