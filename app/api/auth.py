from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession, get_settings
from app.core.config import Settings
from app.schemas.auth import BootstrapAdminRequest, TokenResponse, UserSummary, LoginRequest
from app.services import auth as auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/bootstrap-admin", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    session: DbSession,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    return auth_service.bootstrap_admin(session, payload, settings=settings)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: DbSession,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    return auth_service.login(session, payload, settings=settings)


@router.get("/me", response_model=UserSummary)
def read_me(current_user: CurrentUser) -> UserSummary:
    return auth_service.read_me(current_user)
