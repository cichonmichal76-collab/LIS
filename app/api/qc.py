from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.qc import (
    QcGateDecision,
    QcLotCreateRequest,
    QcLotSummary,
    QcMaterialCreateRequest,
    QcMaterialSummary,
    QcResultCreateRequest,
    QcResultSummary,
    QcRuleCreateRequest,
    QcRuleSummary,
    QcRunCreateRequest,
    QcRunEvaluationResponse,
    QcRunStatus,
    QcRunSummary,
)
from app.services import qc as qc_service

router = APIRouter(prefix="/api/v1/qc", tags=["qc"])


@router.post("/materials", response_model=QcMaterialSummary, status_code=status.HTTP_201_CREATED)
def create_material(
    payload: QcMaterialCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.PATHOLOGIST)),
) -> QcMaterialSummary:
    return qc_service.create_material(session, payload, actor=current_user)


@router.get("/materials", response_model=dict[str, list[QcMaterialSummary]])
def list_materials(
    session: DbSession,
    active: bool | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> dict[str, list[QcMaterialSummary]]:
    return {"items": qc_service.list_materials(session, active=active)}


@router.post("/lots", response_model=QcLotSummary, status_code=status.HTTP_201_CREATED)
def create_lot(
    payload: QcLotCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.PATHOLOGIST)),
) -> QcLotSummary:
    return qc_service.create_lot(session, payload, actor=current_user)


@router.get("/lots", response_model=dict[str, list[QcLotSummary]])
def list_lots(
    session: DbSession,
    active: bool | None = Query(default=None),
    test_catalog_id: UUID | None = Query(default=None),
    device_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> dict[str, list[QcLotSummary]]:
    return {
        "items": qc_service.list_lots(
            session,
            active=active,
            test_catalog_id=test_catalog_id,
            device_id=device_id,
        )
    }


@router.post("/rules", response_model=QcRuleSummary, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: QcRuleCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.PATHOLOGIST)),
) -> QcRuleSummary:
    return qc_service.create_rule(session, payload, actor=current_user)


@router.get("/rules", response_model=dict[str, list[QcRuleSummary]])
def list_rules(
    session: DbSession,
    active: bool | None = Query(default=None),
    test_catalog_id: UUID | None = Query(default=None),
    device_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> dict[str, list[QcRuleSummary]]:
    return {
        "items": qc_service.list_rules(
            session,
            active=active,
            test_catalog_id=test_catalog_id,
            device_id=device_id,
        )
    }


@router.post("/runs", response_model=QcRunSummary, status_code=status.HTTP_201_CREATED)
def create_run(
    payload: QcRunCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)),
) -> QcRunSummary:
    return qc_service.create_run(session, payload, actor=current_user)


@router.get("/runs", response_model=dict[str, list[QcRunSummary]])
def list_runs(
    session: DbSession,
    status_code: QcRunStatus | None = Query(default=None, alias="status"),
    lot_id: UUID | None = Query(default=None),
    device_id: UUID | None = Query(default=None),
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> dict[str, list[QcRunSummary]]:
    return {
        "items": qc_service.list_runs(
            session,
            status_code=status_code,
            lot_id=lot_id,
            device_id=device_id,
        )
    }


@router.get("/runs/{run_id}", response_model=QcRunEvaluationResponse)
def get_run(
    run_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> QcRunEvaluationResponse:
    return qc_service.get_run(session, run_id)


@router.post("/runs/{run_id}/results", response_model=QcResultSummary, status_code=status.HTTP_201_CREATED)
def add_result(
    run_id: UUID,
    payload: QcResultCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)),
) -> QcResultSummary:
    return qc_service.add_result(session, run_id, payload, actor=current_user)


@router.get("/runs/{run_id}/results", response_model=dict[str, list[QcResultSummary]])
def list_results(
    run_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> dict[str, list[QcResultSummary]]:
    return {"items": qc_service.list_results(session, run_id)}


@router.post("/runs/{run_id}/evaluate", response_model=QcRunEvaluationResponse)
def evaluate_run(
    run_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST)),
) -> QcRunEvaluationResponse:
    return qc_service.evaluate_run(session, run_id, actor=current_user)


@router.get("/observations/{observation_id}/gate", response_model=QcGateDecision)
def get_observation_gate(
    observation_id: UUID,
    session: DbSession,
    current_user: UserSummary = Depends(
        require_roles(RoleCode.ADMIN, RoleCode.TECHNICIAN, RoleCode.PATHOLOGIST, RoleCode.VIEWER)
    ),
) -> QcGateDecision:
    return qc_service.get_observation_gate(session, observation_id)
