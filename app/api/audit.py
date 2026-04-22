from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.audit import AuditEventSummary, ProvenanceRecordSummary
from app.services.audit import list_audit_events
from app.services.provenance import list_provenance_records

router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/audit", response_model=dict[str, list[AuditEventSummary]])
def search_audit(
    session: DbSession,
    entity_type: str | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[AuditEventSummary]]:
    return {
        "items": list_audit_events(
            session,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
        )
    }


@router.get("/provenance", response_model=dict[str, list[ProvenanceRecordSummary]])
def search_provenance(
    session: DbSession,
    target_resource_type: str | None = Query(default=None),
    target_resource_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[ProvenanceRecordSummary]]:
    return {
        "items": list_provenance_records(
            session,
            target_resource_type=target_resource_type,
            target_resource_id=str(target_resource_id) if target_resource_id else None,
        )
    }
