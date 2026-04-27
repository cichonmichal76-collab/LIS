from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, get_settings, require_roles
from app.core.config import Settings
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.dashboard import DashboardOverviewResponse
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse, include_in_schema=False)
def get_dashboard_overview(
    session: DbSession,
    settings: Settings = Depends(get_settings),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> DashboardOverviewResponse:
    return dashboard_service.build_overview(session, settings)
