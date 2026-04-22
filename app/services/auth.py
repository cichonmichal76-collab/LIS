from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import UserRecord
from app.schemas.auth import BootstrapAdminRequest, LoginRequest, TokenResponse, UserSummary
from app.services.audit import write_audit_event


def bootstrap_admin(
    session: Session,
    payload: BootstrapAdminRequest,
    *,
    settings: Settings,
) -> TokenResponse:
    user_count = session.scalar(select(func.count()).select_from(UserRecord)) or 0
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bootstrap has already been completed.",
        )

    user = UserRecord(
        id=str(uuid4()),
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role_code="admin",
        active=True,
    )
    session.add(user)
    write_audit_event(
        session,
        entity_type="user",
        entity_id=user.id,
        action="bootstrap-admin",
        status="active",
        actor_user_id=user.id,
        actor_username=user.username,
        actor_role_code=user.role_code,
    )
    session.commit()
    session.refresh(user)
    return _to_token_response(user, settings=settings)


def login(session: Session, payload: LoginRequest, *, settings: Settings) -> TokenResponse:
    user = session.scalar(select(UserRecord).where(UserRecord.username == payload.username))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
    return _to_token_response(user, settings=settings)


def read_me(current_user: UserRecord) -> UserSummary:
    return _to_user_summary(current_user)


def _to_token_response(user: UserRecord, *, settings: Settings) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            subject=user.id,
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            expires_in_minutes=settings.access_token_expire_minutes,
            claims={"role": user.role_code, "username": user.username},
        ),
        user=_to_user_summary(user),
    )


def _to_user_summary(user: UserRecord) -> UserSummary:
    return UserSummary(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role_code=user.role_code,
        active=user.active,
        created_at=user.created_at,
    )
