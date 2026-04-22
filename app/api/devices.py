from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.devices import (
    DeviceCreateRequest,
    DeviceSummary,
    DeviceTestMapCreateRequest,
    DeviceTestMapSummary,
)
from app.services import devices as device_service

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.post("", response_model=DeviceSummary, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN)),
) -> DeviceSummary:
    return device_service.create_device(session, payload, actor=current_user)


@router.get("", response_model=dict[str, list[DeviceSummary]])
def list_devices(
    session: DbSession,
    active: bool | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[DeviceSummary]]:
    return {"items": device_service.list_devices(session, active=active)}


@router.get("/{device_id}", response_model=DeviceSummary)
def get_device(
    device_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> DeviceSummary:
    return device_service.get_device(session, device_id)


@router.post("/{device_id}/mappings", response_model=DeviceTestMapSummary, status_code=status.HTTP_201_CREATED)
def create_device_mapping(
    device_id: UUID,
    payload: DeviceTestMapCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN)),
) -> DeviceTestMapSummary:
    return device_service.create_device_mapping(session, device_id, payload, actor=current_user)


@router.get("/{device_id}/mappings", response_model=dict[str, list[DeviceTestMapSummary]])
def list_device_mappings(
    device_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[DeviceTestMapSummary]]:
    return {"items": device_service.list_device_mappings(session, device_id)}
