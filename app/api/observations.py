from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.observations import (
    CorrectObservationRequest,
    CreateManualObservationRequest,
    ObservationSummary,
    TechnicalVerifyObservationRequest,
)
from app.services import observations as observation_service

router = APIRouter(prefix="/api/v1", tags=["observations"])


@router.post(
    "/observations/manual",
    response_model=ObservationSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_observation(
    payload: CreateManualObservationRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)
    ),
) -> ObservationSummary:
    return observation_service.create_manual_observation(
        session,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.get("/observations", response_model=dict[str, list[ObservationSummary]])
def list_observations(
    session: DbSession,
    specimen_id: UUID | None = Query(default=None),
    order_item_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[ObservationSummary]]:
    return {
        "items": observation_service.list_observations(
            session,
            specimen_id=specimen_id,
            order_item_id=order_item_id,
        )
    }


@router.get("/observations/{observation_id}", response_model=ObservationSummary)
def get_observation(
    observation_id: UUID,
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
) -> ObservationSummary:
    return observation_service.get_observation(session, observation_id)


@router.post(
    "/observations/{observation_id}/technical-verify",
    response_model=ObservationSummary,
)
def technical_verify_observation(
    observation_id: UUID,
    payload: TechnicalVerifyObservationRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)
    ),
) -> ObservationSummary:
    return observation_service.technical_verify_observation(
        session,
        observation_id,
        payload,
        actor_user_id=str(current_user.id),
    )


@router.post("/observations/{observation_id}/correct", response_model=ObservationSummary)
def correct_observation(
    observation_id: UUID,
    payload: CorrectObservationRequest,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)
    ),
) -> ObservationSummary:
    return observation_service.correct_observation(
        session,
        observation_id,
        payload,
        actor_user_id=str(current_user.id),
    )
