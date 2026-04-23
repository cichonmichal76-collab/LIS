from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    DeviceRecord,
    ObservationRecord,
    OrderItemRecord,
    QcLotRecord,
    QcMaterialRecord,
    QcResultRecord,
    QcRuleRecord,
    QcRunRecord,
    RawInstrumentMessageRecord,
    TestCatalogRecord,
)
from app.schemas.auth import UserSummary
from app.schemas.qc import (
    QcDecision,
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
from app.services.audit import write_audit_event


def create_material(
    session: Session,
    payload: QcMaterialCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> QcMaterialSummary:
    material = QcMaterialRecord(
        id=str(uuid4()),
        code=payload.code,
        name=payload.name,
        manufacturer=payload.manufacturer,
        active=payload.active,
    )
    session.add(material)
    write_audit_event(
        session,
        entity_type="qc_material",
        entity_id=material.id,
        action="create",
        status="active" if material.active else "inactive",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"code": material.code},
    )
    session.commit()
    session.refresh(material)
    return _to_material_summary(material)


def list_materials(session: Session, *, active: bool | None = None) -> list[QcMaterialSummary]:
    stmt: Select[tuple[QcMaterialRecord]] = select(QcMaterialRecord).order_by(QcMaterialRecord.code.asc())
    if active is not None:
        stmt = stmt.where(QcMaterialRecord.active == active)
    return [_to_material_summary(item) for item in session.scalars(stmt).all()]


def create_lot(
    session: Session,
    payload: QcLotCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> QcLotSummary:
    _get_material_or_404(session, payload.material_id)
    _get_catalog_or_404(session, payload.test_catalog_id)
    if payload.device_id is not None:
        _get_device_or_404(session, payload.device_id)

    lot = QcLotRecord(
        id=str(uuid4()),
        material_id=str(payload.material_id),
        lot_no=payload.lot_no,
        test_catalog_id=str(payload.test_catalog_id),
        device_id=_optional_uuid(payload.device_id),
        unit_ucum=payload.unit_ucum,
        target_mean=payload.target_mean,
        target_sd=payload.target_sd,
        min_value=payload.min_value,
        max_value=payload.max_value,
        active=payload.active,
        expires_at=payload.expires_at,
    )
    session.add(lot)
    write_audit_event(
        session,
        entity_type="qc_lot",
        entity_id=lot.id,
        action="create",
        status="active" if lot.active else "inactive",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"lot_no": lot.lot_no, "test_catalog_id": lot.test_catalog_id, "device_id": lot.device_id},
    )
    session.commit()
    session.refresh(lot)
    return _to_lot_summary(lot)


def list_lots(
    session: Session,
    *,
    active: bool | None = None,
    test_catalog_id: UUID | None = None,
    device_id: UUID | None = None,
) -> list[QcLotSummary]:
    stmt: Select[tuple[QcLotRecord]] = select(QcLotRecord).order_by(
        QcLotRecord.created_at.desc(),
        QcLotRecord.lot_no.asc(),
    )
    if active is not None:
        stmt = stmt.where(QcLotRecord.active == active)
    if test_catalog_id is not None:
        stmt = stmt.where(QcLotRecord.test_catalog_id == str(test_catalog_id))
    if device_id is not None:
        stmt = stmt.where(QcLotRecord.device_id == str(device_id))
    return [_to_lot_summary(item) for item in session.scalars(stmt).all()]


def create_rule(
    session: Session,
    payload: QcRuleCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> QcRuleSummary:
    if payload.test_catalog_id is not None:
        _get_catalog_or_404(session, payload.test_catalog_id)
    if payload.device_id is not None:
        _get_device_or_404(session, payload.device_id)

    rule = QcRuleRecord(
        id=str(uuid4()),
        name=payload.name,
        active=payload.active,
        priority=payload.priority,
        test_catalog_id=_optional_uuid(payload.test_catalog_id),
        device_id=_optional_uuid(payload.device_id),
        rule_type=payload.rule_type.value,
        params_payload=payload.params,
    )
    session.add(rule)
    write_audit_event(
        session,
        entity_type="qc_rule",
        entity_id=rule.id,
        action="create",
        status="active" if rule.active else "inactive",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"rule_type": rule.rule_type, "priority": rule.priority},
    )
    session.commit()
    session.refresh(rule)
    return _to_rule_summary(rule)


def list_rules(
    session: Session,
    *,
    active: bool | None = None,
    test_catalog_id: UUID | None = None,
    device_id: UUID | None = None,
) -> list[QcRuleSummary]:
    stmt: Select[tuple[QcRuleRecord]] = select(QcRuleRecord).order_by(
        QcRuleRecord.priority.asc(),
        QcRuleRecord.created_at.asc(),
    )
    if active is not None:
        stmt = stmt.where(QcRuleRecord.active == active)
    if test_catalog_id is not None:
        stmt = stmt.where(QcRuleRecord.test_catalog_id == str(test_catalog_id))
    if device_id is not None:
        stmt = stmt.where(QcRuleRecord.device_id == str(device_id))
    return [_to_rule_summary(item) for item in session.scalars(stmt).all()]


def create_run(
    session: Session,
    payload: QcRunCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> QcRunSummary:
    lot = _get_lot_or_404(session, payload.lot_id)
    device_id = _resolve_run_device_id(payload.device_id, lot.device_id)
    if device_id is not None:
        _get_device_or_404(session, UUID(device_id))

    run = QcRunRecord(
        id=str(uuid4()),
        lot_id=lot.id,
        device_id=device_id,
        status=QcRunStatus.OPEN.value,
        started_at=payload.started_at or datetime.now(UTC),
    )
    session.add(run)
    write_audit_event(
        session,
        entity_type="qc_run",
        entity_id=run.id,
        action="create",
        status=run.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"lot_id": run.lot_id, "device_id": run.device_id},
    )
    session.commit()
    session.refresh(run)
    return _to_run_summary(run)


def list_runs(
    session: Session,
    *,
    status_code: QcRunStatus | None = None,
    lot_id: UUID | None = None,
    device_id: UUID | None = None,
) -> list[QcRunSummary]:
    stmt: Select[tuple[QcRunRecord]] = select(QcRunRecord).order_by(QcRunRecord.created_at.desc())
    if status_code is not None:
        stmt = stmt.where(QcRunRecord.status == status_code.value)
    if lot_id is not None:
        stmt = stmt.where(QcRunRecord.lot_id == str(lot_id))
    if device_id is not None:
        stmt = stmt.where(QcRunRecord.device_id == str(device_id))
    return [_to_run_summary(item) for item in session.scalars(stmt).all()]


def get_run(session: Session, run_id: UUID) -> QcRunEvaluationResponse:
    run = _get_run_or_404(session, run_id)
    results = _list_run_results(session, run.id)
    return QcRunEvaluationResponse(
        run=_to_run_summary(run),
        results=[_to_result_summary(item) for item in results],
    )


def add_result(
    session: Session,
    run_id: UUID,
    payload: QcResultCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> QcResultSummary:
    run = _get_run_or_404(session, run_id)
    if run.status != QcRunStatus.OPEN.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"QC run {run_id} is not open for new results.",
        )
    _get_catalog_or_404(session, payload.test_catalog_id)
    if payload.raw_message_id is not None and session.get(RawInstrumentMessageRecord, str(payload.raw_message_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw instrument message {payload.raw_message_id} was not found.",
        )

    result = QcResultRecord(
        id=str(uuid4()),
        run_id=run.id,
        test_catalog_id=str(payload.test_catalog_id),
        value_num=payload.value_num,
        unit_ucum=payload.unit_ucum,
        observed_at=payload.observed_at,
        raw_message_id=_optional_uuid(payload.raw_message_id),
    )
    session.add(result)
    write_audit_event(
        session,
        entity_type="qc_result",
        entity_id=result.id,
        action="create",
        status="recorded",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"run_id": run.id, "test_catalog_id": result.test_catalog_id, "value_num": result.value_num},
    )
    session.commit()
    session.refresh(result)
    return _to_result_summary(result)


def list_results(session: Session, run_id: UUID) -> list[QcResultSummary]:
    _get_run_or_404(session, run_id)
    return [_to_result_summary(item) for item in _list_run_results(session, str(run_id))]


def evaluate_run(
    session: Session,
    run_id: UUID,
    *,
    actor: UserSummary | None = None,
) -> QcRunEvaluationResponse:
    run = _get_run_or_404(session, run_id)
    lot = _get_lot_or_404(session, UUID(run.lot_id))
    results = _list_run_results(session, run.id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"QC run {run_id} cannot be evaluated without QC results.",
        )

    decisions: list[str] = []
    for result in results:
        rules = _list_applicable_rules(
            session,
            test_catalog_id=result.test_catalog_id,
            device_id=run.device_id,
        )
        decision, z_score, warning_rules, failure_rules = _evaluate_result(
            session,
            lot=lot,
            run=run,
            result=result,
            rules=rules,
        )
        result.decision = decision
        result.z_score = z_score
        result.warning_rules_payload = warning_rules
        result.failure_rules_payload = failure_rules
        result.evaluated_at = datetime.now(UTC)
        decisions.append(decision)

    if any(item == QcDecision.FAIL.value for item in decisions):
        run.status = QcRunStatus.FAILED.value
    elif any(item == QcDecision.WARNING.value for item in decisions):
        run.status = QcRunStatus.WARNING.value
    else:
        run.status = QcRunStatus.PASSED.value
    run.evaluated_at = datetime.now(UTC)
    run.reviewed_by_user_id = str(actor.id) if actor else None
    run.summary_payload = {
        "decision_counts": {
            "pass": decisions.count(QcDecision.PASS.value),
            "warning": decisions.count(QcDecision.WARNING.value),
            "fail": decisions.count(QcDecision.FAIL.value),
        },
        "result_count": len(results),
        "lot_id": lot.id,
    }

    write_audit_event(
        session,
        entity_type="qc_run",
        entity_id=run.id,
        action="evaluate",
        status=run.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context=run.summary_payload,
    )
    session.commit()
    session.refresh(run)
    refreshed_results = _list_run_results(session, run.id)
    return QcRunEvaluationResponse(
        run=_to_run_summary(run),
        results=[_to_result_summary(item) for item in refreshed_results],
    )


def get_observation_gate(
    session: Session,
    observation_id: UUID,
) -> QcGateDecision:
    observation = session.get(ObservationRecord, str(observation_id))
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation {observation_id} was not found.",
        )
    order_item = session.get(OrderItemRecord, observation.order_item_id)
    if order_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item {observation.order_item_id} was not found for observation {observation_id}.",
        )
    raw_message = (
        session.get(RawInstrumentMessageRecord, observation.raw_message_id)
        if observation.raw_message_id
        else None
    )
    source_device_id = (raw_message.device_id if raw_message else None) or observation.device_id
    return get_gate_for_scope(
        session,
        test_catalog_id=UUID(order_item.test_catalog_id),
        device_id=UUID(source_device_id) if source_device_id else None,
    )


def get_gate_for_scope(
    session: Session,
    *,
    test_catalog_id: UUID,
    device_id: UUID | None = None,
) -> QcGateDecision:
    _get_catalog_or_404(session, test_catalog_id)
    if device_id is not None:
        _get_device_or_404(session, device_id)
    return _evaluate_gate(
        session,
        test_catalog_id=str(test_catalog_id),
        device_id=str(device_id) if device_id else None,
    )


def _evaluate_gate(
    session: Session,
    *,
    test_catalog_id: str,
    device_id: str | None,
) -> QcGateDecision:
    applicable_lots = _list_active_lots_for_scope(
        session,
        test_catalog_id=test_catalog_id,
        device_id=device_id,
    )
    if not applicable_lots:
        return QcGateDecision(applies=False, allowed=True)

    latest_result = session.scalar(
        _latest_qc_result_stmt(test_catalog_id=test_catalog_id, device_id=device_id)
    )
    if latest_result is None:
        return QcGateDecision(
            applies=True,
            allowed=False,
            reasons=["QC is configured for this test scope but no evaluated QC run is available."],
        )

    latest_run = session.get(QcRunRecord, latest_result.run_id)
    latest_decision = latest_result.decision
    if latest_run is None or latest_decision is None:
        return QcGateDecision(
            applies=True,
            allowed=False,
            reasons=["Latest QC result is incomplete and cannot be used for release gating."],
            latest_result_id=latest_result.id,
        )

    if latest_decision == QcDecision.FAIL.value or latest_run.status == QcRunStatus.FAILED.value:
        return QcGateDecision(
            applies=True,
            allowed=False,
            reasons=[
                f"Latest QC result for this scope failed in run {latest_run.id}.",
            ],
            latest_run_id=latest_run.id,
            latest_result_id=latest_result.id,
            latest_decision=latest_decision,
        )

    return QcGateDecision(
        applies=True,
        allowed=True,
        latest_run_id=latest_run.id,
        latest_result_id=latest_result.id,
        latest_decision=latest_decision,
    )


def _list_active_lots_for_scope(
    session: Session,
    *,
    test_catalog_id: str,
    device_id: str | None,
) -> list[QcLotRecord]:
    now = datetime.now(UTC)
    stmt = (
        select(QcLotRecord)
        .where(QcLotRecord.active.is_(True))
        .where(QcLotRecord.test_catalog_id == test_catalog_id)
        .where((QcLotRecord.expires_at.is_(None)) | (QcLotRecord.expires_at >= now))
        .order_by(QcLotRecord.created_at.desc())
    )
    if device_id is None:
        stmt = stmt.where(QcLotRecord.device_id.is_(None))
    else:
        stmt = stmt.where((QcLotRecord.device_id.is_(None)) | (QcLotRecord.device_id == device_id))
    return session.scalars(stmt).all()


def _latest_qc_result_stmt(
    *,
    test_catalog_id: str,
    device_id: str | None,
) -> Select[tuple[QcResultRecord]]:
    now = datetime.now(UTC)
    stmt: Select[tuple[QcResultRecord]] = (
        select(QcResultRecord)
        .join(QcRunRecord, QcResultRecord.run_id == QcRunRecord.id)
        .join(QcLotRecord, QcRunRecord.lot_id == QcLotRecord.id)
        .where(QcResultRecord.test_catalog_id == test_catalog_id)
        .where(QcResultRecord.decision.is_not(None))
        .where(QcLotRecord.active.is_(True))
        .where((QcLotRecord.expires_at.is_(None)) | (QcLotRecord.expires_at >= now))
        .order_by(
            func.coalesce(QcResultRecord.evaluated_at, QcResultRecord.created_at).desc(),
            QcResultRecord.created_at.desc(),
        )
    )
    if device_id is None:
        stmt = stmt.where(QcLotRecord.device_id.is_(None))
    else:
        stmt = stmt.where((QcLotRecord.device_id.is_(None)) | (QcLotRecord.device_id == device_id))
    return stmt


def _evaluate_result(
    session: Session,
    *,
    lot: QcLotRecord,
    run: QcRunRecord,
    result: QcResultRecord,
    rules: list[QcRuleRecord],
) -> tuple[str, float | None, list[str], list[str]]:
    warning_rules: list[str] = []
    failure_rules: list[str] = []

    if lot.unit_ucum and result.unit_ucum and lot.unit_ucum != result.unit_ucum:
        failure_rules.append(f"unit-mismatch:{lot.unit_ucum}")

    if lot.min_value is not None and float(result.value_num) < float(lot.min_value):
        failure_rules.append("lot-range")
    if lot.max_value is not None and float(result.value_num) > float(lot.max_value):
        failure_rules.append("lot-range")

    z_score = _calculate_z_score(result.value_num, lot.target_mean, lot.target_sd)
    recent_results = _recent_previous_results(
        session,
        run_id=run.id,
        result_id=result.id,
        test_catalog_id=result.test_catalog_id,
        limit=4,
    )
    previous_result = recent_results[0] if recent_results else None
    previous_z = previous_result.z_score if previous_result else None
    recent_z_scores = [item.z_score for item in recent_results if item.z_score is not None]

    for rule in rules:
        triggered = _evaluate_rule_trigger(
            rule=rule,
            result=result,
            lot=lot,
            z_score=z_score,
            previous_z=previous_z,
            recent_z_scores=recent_z_scores,
        )
        if triggered == QcDecision.FAIL.value:
            failure_rules.append(rule.name)
        elif triggered == QcDecision.WARNING.value:
            warning_rules.append(rule.name)

    if failure_rules:
        return QcDecision.FAIL.value, z_score, sorted(set(warning_rules)), sorted(set(failure_rules))
    if warning_rules:
        return QcDecision.WARNING.value, z_score, sorted(set(warning_rules)), []
    return QcDecision.PASS.value, z_score, [], []


def _evaluate_rule_trigger(
    *,
    rule: QcRuleRecord,
    result: QcResultRecord,
    lot: QcLotRecord,
    z_score: float | None,
    previous_z: float | None,
    recent_z_scores: list[float],
) -> str | None:
    params = rule.params_payload or {}
    if rule.rule_type == "range":
        min_value = float(params["min_value"]) if params.get("min_value") is not None else lot.min_value
        max_value = float(params["max_value"]) if params.get("max_value") is not None else lot.max_value
        if min_value is not None and float(result.value_num) < float(min_value):
            return QcDecision.FAIL.value
        if max_value is not None and float(result.value_num) > float(max_value):
            return QcDecision.FAIL.value
        return None

    if rule.rule_type == "westgard_12s":
        if z_score is not None and abs(z_score) > 2.0:
            return QcDecision.WARNING.value
        return None

    if rule.rule_type == "westgard_13s":
        if z_score is not None and abs(z_score) > 3.0:
            return QcDecision.FAIL.value
        return None

    if rule.rule_type == "westgard_22s":
        if z_score is None or previous_z is None:
            return None
        if abs(z_score) > 2.0 and abs(previous_z) > 2.0 and (z_score > 0) == (previous_z > 0):
            return QcDecision.FAIL.value
        return None

    if rule.rule_type == "westgard_r4s":
        if z_score is None or previous_z is None:
            return None
        if abs(z_score) > 2.0 and abs(previous_z) > 2.0 and (z_score > 0) != (previous_z > 0):
            return QcDecision.FAIL.value
        return None

    if rule.rule_type == "westgard_41s":
        if z_score is None:
            return None
        series = [z_score, *recent_z_scores[:3]]
        if len(series) < 4:
            return None
        if all(item > 1.0 for item in series) or all(item < -1.0 for item in series):
            return QcDecision.FAIL.value
        return None

    return None


def _recent_previous_results(
    session: Session,
    *,
    run_id: str,
    result_id: str,
    test_catalog_id: str,
    limit: int,
) -> list[QcResultRecord]:
    run = session.get(QcRunRecord, run_id)
    if run is None:
        return []
    lot_id = run.lot_id
    return session.scalars(
        select(QcResultRecord)
        .join(QcRunRecord, QcResultRecord.run_id == QcRunRecord.id)
        .where(QcRunRecord.lot_id == lot_id)
        .where(QcResultRecord.test_catalog_id == test_catalog_id)
        .where(QcResultRecord.id != result_id)
        .where(QcResultRecord.evaluated_at.is_not(None))
        .order_by(
            func.coalesce(QcResultRecord.evaluated_at, QcResultRecord.created_at).desc(),
            QcResultRecord.created_at.desc(),
        )
        .limit(limit)
    ).all()


def _calculate_z_score(value: float, mean: float | None, sd: float | None) -> float | None:
    if mean is None or sd is None or float(sd) == 0:
        return None
    return (float(value) - float(mean)) / float(sd)


def _list_applicable_rules(
    session: Session,
    *,
    test_catalog_id: str,
    device_id: str | None,
) -> list[QcRuleRecord]:
    stmt = (
        select(QcRuleRecord)
        .where(QcRuleRecord.active.is_(True))
        .order_by(QcRuleRecord.priority.asc(), QcRuleRecord.created_at.asc())
    )
    stmt = stmt.where((QcRuleRecord.test_catalog_id.is_(None)) | (QcRuleRecord.test_catalog_id == test_catalog_id))
    if device_id is None:
        stmt = stmt.where(QcRuleRecord.device_id.is_(None))
    else:
        stmt = stmt.where((QcRuleRecord.device_id.is_(None)) | (QcRuleRecord.device_id == device_id))
    return session.scalars(stmt).all()


def _resolve_run_device_id(requested_device_id: UUID | None, lot_device_id: str | None) -> str | None:
    if requested_device_id is None:
        return lot_device_id
    if lot_device_id is not None and str(requested_device_id) != lot_device_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="QC run device does not match the device scope configured on the QC lot.",
        )
    return str(requested_device_id)


def _list_run_results(session: Session, run_id: str) -> list[QcResultRecord]:
    return session.scalars(
        select(QcResultRecord)
        .where(QcResultRecord.run_id == run_id)
        .order_by(QcResultRecord.created_at.asc())
    ).all()


def _get_material_or_404(session: Session, material_id: UUID) -> QcMaterialRecord:
    material = session.get(QcMaterialRecord, str(material_id))
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QC material {material_id} was not found.",
        )
    return material


def _get_catalog_or_404(session: Session, test_catalog_id: UUID) -> TestCatalogRecord:
    catalog = session.get(TestCatalogRecord, str(test_catalog_id))
    if catalog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item {test_catalog_id} was not found.",
        )
    return catalog


def _get_device_or_404(session: Session, device_id: UUID) -> DeviceRecord:
    device = session.get(DeviceRecord, str(device_id))
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} was not found.",
        )
    return device


def _get_lot_or_404(session: Session, lot_id: UUID) -> QcLotRecord:
    lot = session.get(QcLotRecord, str(lot_id))
    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QC lot {lot_id} was not found.",
        )
    return lot


def _get_run_or_404(session: Session, run_id: UUID) -> QcRunRecord:
    run = session.get(QcRunRecord, str(run_id))
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QC run {run_id} was not found.",
        )
    return run


def _to_material_summary(material: QcMaterialRecord) -> QcMaterialSummary:
    return QcMaterialSummary(
        id=material.id,
        code=material.code,
        name=material.name,
        manufacturer=material.manufacturer,
        active=material.active,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


def _to_lot_summary(lot: QcLotRecord) -> QcLotSummary:
    return QcLotSummary(
        id=lot.id,
        material_id=lot.material_id,
        lot_no=lot.lot_no,
        test_catalog_id=lot.test_catalog_id,
        device_id=lot.device_id,
        unit_ucum=lot.unit_ucum,
        target_mean=lot.target_mean,
        target_sd=lot.target_sd,
        min_value=lot.min_value,
        max_value=lot.max_value,
        active=lot.active,
        expires_at=lot.expires_at,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
    )


def _to_rule_summary(rule: QcRuleRecord) -> QcRuleSummary:
    return QcRuleSummary(
        id=rule.id,
        name=rule.name,
        active=rule.active,
        priority=rule.priority,
        test_catalog_id=rule.test_catalog_id,
        device_id=rule.device_id,
        rule_type=rule.rule_type,
        params=rule.params_payload,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _to_run_summary(run: QcRunRecord) -> QcRunSummary:
    return QcRunSummary(
        id=run.id,
        lot_id=run.lot_id,
        device_id=run.device_id,
        status=run.status,
        started_at=run.started_at,
        evaluated_at=run.evaluated_at,
        reviewed_by_user_id=run.reviewed_by_user_id,
        summary=run.summary_payload,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _to_result_summary(result: QcResultRecord) -> QcResultSummary:
    return QcResultSummary(
        id=result.id,
        run_id=result.run_id,
        test_catalog_id=result.test_catalog_id,
        value_num=result.value_num,
        unit_ucum=result.unit_ucum,
        decision=result.decision,
        z_score=result.z_score,
        warning_rules=result.warning_rules_payload,
        failure_rules=result.failure_rules_payload,
        observed_at=result.observed_at,
        evaluated_at=result.evaluated_at,
        raw_message_id=result.raw_message_id,
        created_at=result.created_at,
    )


def _optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None
