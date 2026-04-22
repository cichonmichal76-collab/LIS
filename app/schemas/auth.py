from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from app.schemas.common import ApiModel

Password = Annotated[str, StringConstraints(min_length=8)]


class RoleCode(str, Enum):
    ADMIN = "admin"
    ACCESSIONER = "accessioner"
    TECHNICIAN = "technician"
    PATHOLOGIST = "pathologist"
    VIEWER = "viewer"


class BootstrapAdminRequest(ApiModel):
    username: str
    password: Password
    display_name: str


class LoginRequest(ApiModel):
    username: str
    password: str


class UserSummary(ApiModel):
    id: UUID
    username: str
    display_name: str
    role_code: RoleCode
    active: bool
    created_at: datetime


class TokenResponse(ApiModel):
    access_token: str
    token_type: str = Field(default="bearer")
    user: UserSummary
