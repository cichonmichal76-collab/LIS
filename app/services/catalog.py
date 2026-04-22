from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import TestCatalogRecord
from app.schemas.auth import UserSummary
from app.schemas.catalog import TestCatalogCreateRequest, TestCatalogSummary
from app.services.audit import write_audit_event


def create_test_catalog_item(
    session: Session,
    payload: TestCatalogCreateRequest,
    *,
    actor: UserSummary,
) -> TestCatalogSummary:
    existing = session.scalar(select(TestCatalogRecord).where(TestCatalogRecord.local_code == payload.local_code))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Catalog code '{payload.local_code}' already exists.",
        )

    item = TestCatalogRecord(
        id=str(uuid4()),
        local_code=payload.local_code,
        display_name=payload.display_name,
        kind=payload.kind.value,
        loinc_num=payload.loinc_num,
        specimen_type_code=payload.specimen_type_code,
        default_ucum=payload.default_ucum,
        result_value_type=payload.result_value_type.value,
        active=True,
    )
    session.add(item)
    write_audit_event(
        session,
        entity_type="test-catalog",
        entity_id=item.id,
        action="create",
        status="active",
        actor_user_id=str(actor.id),
        actor_username=actor.username,
        actor_role_code=actor.role_code.value,
        context={"local_code": item.local_code},
    )
    session.commit()
    session.refresh(item)
    return _to_test_catalog_summary(item)


def list_test_catalog(
    session: Session,
    *,
    local_code: str | None = None,
    q: str | None = None,
) -> list[TestCatalogSummary]:
    stmt: Select[tuple[TestCatalogRecord]] = select(TestCatalogRecord).order_by(
        TestCatalogRecord.display_name.asc()
    )
    if local_code:
        stmt = stmt.where(TestCatalogRecord.local_code == local_code)
    if q:
        query = f"%{q}%"
        stmt = stmt.where(
            TestCatalogRecord.display_name.ilike(query) | TestCatalogRecord.local_code.ilike(query)
        )
    return [_to_test_catalog_summary(item) for item in session.scalars(stmt).all()]


def get_test_catalog_item(session: Session, catalog_id: UUID) -> TestCatalogSummary:
    item = session.get(TestCatalogRecord, str(catalog_id))
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item {catalog_id} was not found.",
        )
    return _to_test_catalog_summary(item)


def _to_test_catalog_summary(item: TestCatalogRecord) -> TestCatalogSummary:
    return TestCatalogSummary(
        id=item.id,
        local_code=item.local_code,
        display_name=item.display_name,
        kind=item.kind,
        loinc_num=item.loinc_num,
        specimen_type_code=item.specimen_type_code,
        default_ucum=item.default_ucum,
        result_value_type=item.result_value_type,
        active=item.active,
        created_at=item.created_at,
    )
