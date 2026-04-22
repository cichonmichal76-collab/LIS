from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import decode_access_token
from app.db.models import UserRecord
from app.schemas.auth import RoleCode, UserSummary

bearer_scheme = HTTPBearer(auto_error=False)


def get_db_session(request: Request):
    session_factory = request.app.state.db.session_factory
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db_session)]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_current_user(
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserSummary:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    try:
        payload = decode_access_token(
            token=credentials.credentials,
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is missing.",
        )

    user = session.get(UserRecord, str(user_id))
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    return UserSummary(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role_code=user.role_code,
        active=user.active,
        created_at=user.created_at,
    )


CurrentUser = Annotated[UserSummary, Depends(get_current_user)]


def require_roles(*roles: RoleCode | str) -> Callable[[CurrentUser], UserSummary]:
    allowed_roles = {role.value if isinstance(role, RoleCode) else role for role in roles}

    def dependency(current_user: CurrentUser) -> UserSummary:
        if current_user.role_code.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role.",
            )
        return current_user

    return dependency
