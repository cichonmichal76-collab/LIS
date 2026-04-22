from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.catalog import TestCatalogCreateRequest, TestCatalogSummary
from app.services import catalog as catalog_service

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.post("/test-catalog", response_model=TestCatalogSummary, status_code=status.HTTP_201_CREATED)
def create_test_catalog_item(
    payload: TestCatalogCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN)),
) -> TestCatalogSummary:
    return catalog_service.create_test_catalog_item(session, payload, actor=current_user)


@router.get("/test-catalog", response_model=dict[str, list[TestCatalogSummary]])
def list_catalog(
    session: DbSession,
    local_code: str | None = Query(default=None),
    q: str | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[TestCatalogSummary]]:
    return {"items": catalog_service.list_test_catalog(session, local_code=local_code, q=q)}


@router.get("/test-catalog/{catalog_id}", response_model=TestCatalogSummary)
def get_catalog_item(
    catalog_id: UUID,
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
) -> TestCatalogSummary:
    return catalog_service.get_test_catalog_item(session, catalog_id)
