from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ApiError(ApiModel):
    detail: str


class HealthResponse(ApiModel):
    service: str
    status: str
    version: str
    contract_path: str

