from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.autoverification import (
    AutoverificationApplyResponse,
    AutoverificationEvaluateResponse,
    AutoverificationRuleCreateRequest,
    AutoverificationRuleSummary,
    AutoverificationRunSummary,
)
from app.services import autoverification as autoverification_service

router = APIRouter(prefix="/api/v1/autoverification", tags=["autoverification"])


@router.post("/rules", response_model=AutoverificationRuleSummary, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: AutoverificationRuleCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.PATHOLOGIST)),
) -> AutoverificationRuleSummary:
    return autoverification_service.create_rule(session, payload, actor=current_user)


@router.get("/rules", response_model=dict[str, list[AutoverificationRuleSummary]])
def list_rules(
    session: DbSession,
    active: bool | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[AutoverificationRuleSummary]]:
    return {"items": autoverification_service.list_rules(session, active=active)}


@router.get("/rules/{rule_id}", response_model=AutoverificationRuleSummary)
def get_rule(
    rule_id: UUID,
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
) -> AutoverificationRuleSummary:
    return autoverification_service.get_rule(session, rule_id)


@router.post("/observations/{observation_id}/evaluate", response_model=AutoverificationEvaluateResponse)
def evaluate_observation(
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
) -> AutoverificationEvaluateResponse:
    return autoverification_service.evaluate_observation(session, observation_id)


@router.post("/observations/{observation_id}/apply", response_model=AutoverificationApplyResponse)
def apply_autoverification(
    observation_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)
    ),
) -> AutoverificationApplyResponse:
    return autoverification_service.apply_autoverification(
        session,
        observation_id,
        actor=current_user,
    )


@router.get("/observations/{observation_id}/runs", response_model=dict[str, list[AutoverificationRunSummary]])
def list_runs(
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
) -> dict[str, list[AutoverificationRunSummary]]:
    return {"items": autoverification_service.list_runs(session, observation_id)}
