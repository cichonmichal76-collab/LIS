from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import DeviceRecord, DeviceTestMapRecord, TestCatalogRecord
from app.schemas.auth import UserSummary
from app.schemas.devices import (
    DeviceCreateRequest,
    DeviceSummary,
    DeviceTestMapCreateRequest,
    DeviceTestMapSummary,
)
from app.services.audit import write_audit_event


def create_device(
    session: Session,
    payload: DeviceCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> DeviceSummary:
    existing = session.scalar(select(DeviceRecord).where(DeviceRecord.code == payload.code))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device code '{payload.code}' already exists.",
        )

    device = DeviceRecord(
        id=str(uuid4()),
        code=payload.code,
        name=payload.name,
        manufacturer=payload.manufacturer,
        model=payload.model,
        serial_no=payload.serial_no,
        protocol_code=payload.protocol_code,
        active=True,
    )
    session.add(device)
    write_audit_event(
        session,
        entity_type="device",
        entity_id=device.id,
        action="create",
        status="active",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"code": device.code, "protocol_code": device.protocol_code},
    )
    session.commit()
    session.refresh(device)
    return _to_device_summary(device)


def list_devices(session: Session, *, active: bool | None = None) -> list[DeviceSummary]:
    stmt: Select[tuple[DeviceRecord]] = select(DeviceRecord).order_by(DeviceRecord.code.asc())
    if active is not None:
        stmt = stmt.where(DeviceRecord.active == active)
    return [_to_device_summary(device) for device in session.scalars(stmt).all()]


def get_device(session: Session, device_id: UUID) -> DeviceSummary:
    device = _get_device_or_404(session, device_id)
    return _to_device_summary(device)


def create_device_mapping(
    session: Session,
    device_id: UUID,
    payload: DeviceTestMapCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> DeviceTestMapSummary:
    device = _get_device_or_404(session, device_id)
    if not device.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device {device_id} is inactive.",
        )

    catalog = session.get(TestCatalogRecord, str(payload.test_catalog_id))
    if catalog is None or not catalog.active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item {payload.test_catalog_id} was not found.",
        )

    existing = session.scalar(
        select(DeviceTestMapRecord).where(
            DeviceTestMapRecord.device_id == device.id,
            DeviceTestMapRecord.incoming_test_code == payload.incoming_test_code,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mapping already exists for device and incoming test code.",
        )

    mapping = DeviceTestMapRecord(
        id=str(uuid4()),
        device_id=device.id,
        incoming_test_code=payload.incoming_test_code,
        test_catalog_id=catalog.id,
        default_unit_ucum=payload.default_unit_ucum,
        active=True,
    )
    session.add(mapping)
    write_audit_event(
        session,
        entity_type="device_test_map",
        entity_id=mapping.id,
        action="create",
        status="active",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={
            "device_id": device.id,
            "incoming_test_code": mapping.incoming_test_code,
            "test_catalog_id": catalog.id,
        },
    )
    session.commit()
    session.refresh(mapping)
    return _to_device_test_map_summary(mapping, catalog)


def list_device_mappings(session: Session, device_id: UUID) -> list[DeviceTestMapSummary]:
    _get_device_or_404(session, device_id)
    mappings = session.scalars(
        select(DeviceTestMapRecord)
        .where(DeviceTestMapRecord.device_id == str(device_id))
        .order_by(DeviceTestMapRecord.incoming_test_code.asc())
    ).all()
    catalog_ids = {mapping.test_catalog_id for mapping in mappings}
    catalog_lookup = {
        item.id: item
        for item in session.scalars(
            select(TestCatalogRecord).where(TestCatalogRecord.id.in_(catalog_ids))
        ).all()
    }
    return [
        _to_device_test_map_summary(mapping, catalog_lookup[mapping.test_catalog_id])
        for mapping in mappings
        if mapping.test_catalog_id in catalog_lookup
    ]


def _get_device_or_404(session: Session, device_id: UUID) -> DeviceRecord:
    device = session.get(DeviceRecord, str(device_id))
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} was not found.",
        )
    return device


def _to_device_summary(device: DeviceRecord) -> DeviceSummary:
    return DeviceSummary(
        id=device.id,
        code=device.code,
        name=device.name,
        manufacturer=device.manufacturer,
        model=device.model,
        serial_no=device.serial_no,
        protocol_code=device.protocol_code,
        active=device.active,
        created_at=device.created_at,
    )


def _to_device_test_map_summary(
    mapping: DeviceTestMapRecord,
    catalog: TestCatalogRecord,
) -> DeviceTestMapSummary:
    return DeviceTestMapSummary(
        id=mapping.id,
        device_id=mapping.device_id,
        incoming_test_code=mapping.incoming_test_code,
        test_catalog_id=mapping.test_catalog_id,
        default_unit_ucum=mapping.default_unit_ucum,
        active=mapping.active,
        local_code=catalog.local_code,
        display_name=catalog.display_name,
        loinc_num=catalog.loinc_num,
        created_at=mapping.created_at,
    )
