from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.reports import (
    AmendReportRequest,
    AuthorizeReportRequest,
    CreateReportRequest,
    DiagnosticReportSummary,
)
from app.services import reports as report_service

router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.post(
    "/reports/generate",
    response_model=DiagnosticReportSummary,
    status_code=status.HTTP_201_CREATED,
)
def generate_report(
    payload: CreateReportRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)
    ),
) -> DiagnosticReportSummary:
    return report_service.generate_report(
        session,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.get("/reports/{report_id}", response_model=DiagnosticReportSummary)
def get_report(
    report_id: UUID,
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
) -> DiagnosticReportSummary:
    return report_service.get_report(session, report_id)


@router.post("/reports/{report_id}/authorize", response_model=DiagnosticReportSummary)
def authorize_report(
    report_id: UUID,
    payload: AuthorizeReportRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.PATHOLOGIST)),
) -> DiagnosticReportSummary:
    if str(payload.signed_by_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Signed-by user must match the authenticated user.")
    return report_service.authorize_report(
        session,
        report_id,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.post("/reports/{report_id}/amend", response_model=DiagnosticReportSummary)
def amend_report(
    report_id: UUID,
    payload: AmendReportRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.PATHOLOGIST)),
) -> DiagnosticReportSummary:
    if str(payload.signed_by_user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Signed-by user must match the authenticated user.")
    return report_service.amend_report(
        session,
        report_id,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.get(
    "/reports/{report_id}/pdf",
    responses={200: {"content": {"application/pdf": {}}}},
)
def get_report_pdf(
    report_id: UUID,
    session: DbSession,
    version: int | None = Query(default=None, ge=1),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> Response:
    pdf_bytes = report_service.render_report_pdf(session, report_id, version_no=version)
    return Response(content=pdf_bytes, media_type="application/pdf")
