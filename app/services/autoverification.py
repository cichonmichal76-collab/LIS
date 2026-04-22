from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AutoverificationRuleRecord,
    AutoverificationRunRecord,
    DeviceRecord,
    ObservationRecord,
    OrderItemRecord,
    OrderRecord,
    RawInstrumentMessageRecord,
    SpecimenRecord,
    TaskRecord,
    TestCatalogRecord,
)
from app.schemas.auth import UserSummary
from app.schemas.autoverification import (
    AutoverificationApplyDecision,
    AutoverificationApplyResponse,
    AutoverificationCheckDecision,
    AutoverificationEvaluateResponse,
    AutoverificationRuleCreateRequest,
    AutoverificationRuleEvaluation,
    AutoverificationRuleSummary,
    AutoverificationRunSummary,
)
from app.services.audit import write_audit_event
from app.services.provenance import write_provenance_record

ALLOWED_REVIEW_TASK_STATUSES = {"created", "ready", "in_progress", "on_hold"}


def create_rule(
    session: Session,
    payload: AutoverificationRuleCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> AutoverificationRuleSummary:
    if payload.test_catalog_id is not None and session.get(TestCatalogRecord, str(payload.test_catalog_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item {payload.test_catalog_id} was not found.",
        )
    if payload.device_id is not None and session.get(DeviceRecord, str(payload.device_id)) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {payload.device_id} was not found.",
        )

    rule = AutoverificationRuleRecord(
        id=str(uuid4()),
        name=payload.name,
        active=payload.active,
        priority=payload.priority,
        test_catalog_id=_optional_uuid(payload.test_catalog_id),
        device_id=_optional_uuid(payload.device_id),
        specimen_type_code=payload.specimen_type_code,
        rule_type=payload.rule_type.value,
        condition_payload=payload.condition,
    )
    session.add(rule)
    write_audit_event(
        session,
        entity_type="autoverification_rule",
        entity_id=rule.id,
        action="create",
        status="active" if rule.active else "inactive",
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"priority": rule.priority, "rule_type": rule.rule_type},
    )
    session.commit()
    session.refresh(rule)
    return _to_rule_summary(rule)


def list_rules(session: Session, *, active: bool | None = None) -> list[AutoverificationRuleSummary]:
    stmt: Select[tuple[AutoverificationRuleRecord]] = select(AutoverificationRuleRecord).order_by(
        AutoverificationRuleRecord.priority.asc(),
        AutoverificationRuleRecord.created_at.asc(),
    )
    if active is not None:
        stmt = stmt.where(AutoverificationRuleRecord.active == active)
    return [_to_rule_summary(rule) for rule in session.scalars(stmt).all()]


def get_rule(session: Session, rule_id: UUID) -> AutoverificationRuleSummary:
    rule = _get_rule_or_404(session, rule_id)
    return _to_rule_summary(rule)


def evaluate_observation(
    session: Session,
    observation_id: UUID,
) -> AutoverificationEvaluateResponse:
    context = _get_observation_context(session, observation_id)
    previous_final = _latest_previous_final(session, context)
    rules = _list_applicable_rules(session, context)
    evaluated_rules = [_evaluate_rule(rule, context, previous_final) for rule in rules]

    implicit_reasons: list[str] = []
    if context["specimen_status"] in {"rejected", "disposed"}:
        implicit_reasons.append(
            f"specimen status {context['specimen_status']!r} blocks autoverification"
        )
    if context["observation"].value_type == "quantity" and context["observation"].value_num is None:
        implicit_reasons.append("quantity result has no numeric value")
    if context["observation"].status == "cancelled":
        implicit_reasons.append("cancelled observation cannot be auto-finalized")

    all_rule_pass = all(rule.decision is AutoverificationCheckDecision.PASS for rule in evaluated_rules)
    overall_decision = (
        AutoverificationCheckDecision.PASS
        if not implicit_reasons and all_rule_pass
        else AutoverificationCheckDecision.FAIL
    )
    return AutoverificationEvaluateResponse(
        observation_id=context["observation"].id,
        previous_final_observation_id=previous_final.id if previous_final else None,
        overall_decision=overall_decision,
        matched_rule_count=len(evaluated_rules),
        implicit_reasons=implicit_reasons,
        rules=evaluated_rules,
    )


def apply_autoverification(
    session: Session,
    observation_id: UUID,
    *,
    actor: UserSummary | None = None,
    source_activity: str = "autoverification",
) -> AutoverificationApplyResponse:
    session.flush()
    evaluation = evaluate_observation(session, observation_id)
    context = _get_observation_context(session, observation_id)
    observation = context["observation"]
    order_item = context["order_item"]
    specimen = context["specimen"]

    summary_reasons = list(evaluation.implicit_reasons)
    for rule in evaluation.rules:
        summary_reasons.extend(rule.reasons)

    created_task: TaskRecord | None = None
    if evaluation.overall_decision is AutoverificationCheckDecision.PASS:
        observation.status = "final"
        observation.issued_at = datetime.now(UTC)
        order_item.status = "released"
        decision = AutoverificationApplyDecision.AUTO_FINALIZED
        write_provenance_record(
            session,
            target_resource_type="observation",
            target_resource_id=observation.id,
            activity_code=f"{source_activity}-finalize",
            based_on_order_id=context["order"].id,
            based_on_order_item_id=order_item.id,
            specimen_id=specimen.id if specimen else None,
            observation_id=observation.id,
            device_id=context["source_device_id"],
            agent_user_id=str(actor.id) if actor else None,
            inputs={
                "matched_rule_count": evaluation.matched_rule_count,
                "rule_ids": [str(rule.rule_id) for rule in evaluation.rules],
            },
        )
    else:
        observation.status = "preliminary"
        observation.issued_at = None
        order_item.status = "tech_review"
        created_task = _ensure_review_task(
            session,
            observation=observation,
            order_item=order_item,
            device_id=context["source_device_id"],
            reasons=summary_reasons,
        )
        decision = AutoverificationApplyDecision.HELD
        write_provenance_record(
            session,
            target_resource_type="observation",
            target_resource_id=observation.id,
            activity_code=f"{source_activity}-hold",
            based_on_order_id=context["order"].id,
            based_on_order_item_id=order_item.id,
            specimen_id=specimen.id if specimen else None,
            observation_id=observation.id,
            device_id=context["source_device_id"],
            agent_user_id=str(actor.id) if actor else None,
            inputs={
                "reasons": summary_reasons,
                "created_task_id": created_task.id,
            },
        )

    _persist_run_rows(
        session,
        observation_id=observation.id,
        evaluation=evaluation,
        decision=decision,
        created_task_id=created_task.id if created_task else None,
    )
    write_audit_event(
        session,
        entity_type="observation",
        entity_id=observation.id,
        action="autoverification-apply",
        status=observation.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={
            "decision": decision.value,
            "matched_rule_count": evaluation.matched_rule_count,
            "created_task_id": created_task.id if created_task else None,
            "reasons": summary_reasons,
        },
    )
    session.commit()
    session.refresh(observation)
    return AutoverificationApplyResponse(
        observation_id=observation.id,
        decision=decision,
        matched_rule_count=evaluation.matched_rule_count,
        reasons=summary_reasons,
        created_task_id=created_task.id if created_task else None,
        rules=evaluation.rules,
    )


def list_runs(
    session: Session,
    observation_id: UUID,
) -> list[AutoverificationRunSummary]:
    _get_observation_or_404(session, observation_id)
    runs = session.scalars(
        select(AutoverificationRunRecord)
        .where(AutoverificationRunRecord.observation_id == str(observation_id))
        .order_by(AutoverificationRunRecord.evaluated_at.desc(), AutoverificationRunRecord.id.desc())
    ).all()
    return [_to_run_summary(run) for run in runs]


def _get_rule_or_404(session: Session, rule_id: UUID) -> AutoverificationRuleRecord:
    rule = session.get(AutoverificationRuleRecord, str(rule_id))
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Autoverification rule {rule_id} was not found.",
        )
    return rule


def _get_observation_or_404(session: Session, observation_id: UUID) -> ObservationRecord:
    observation = session.get(ObservationRecord, str(observation_id))
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation {observation_id} was not found.",
        )
    return observation


def _get_observation_context(session: Session, observation_id: UUID) -> dict[str, Any]:
    observation = _get_observation_or_404(session, observation_id)
    order_item = session.get(OrderItemRecord, observation.order_item_id)
    if order_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item {observation.order_item_id} was not found for observation {observation_id}.",
        )
    order = session.get(OrderRecord, order_item.order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_item.order_id} was not found for observation {observation_id}.",
        )
    specimen = session.get(SpecimenRecord, observation.specimen_id) if observation.specimen_id else None
    raw_message = (
        session.get(RawInstrumentMessageRecord, observation.raw_message_id)
        if observation.raw_message_id
        else None
    )
    return {
        "observation": observation,
        "order_item": order_item,
        "order": order,
        "specimen": specimen,
        "patient_id": order.patient_id,
        "test_catalog_id": order_item.test_catalog_id,
        "specimen_status": specimen.status if specimen else None,
        "specimen_type_code": specimen.specimen_type_code if specimen else None,
        "source_device_id": (raw_message.device_id if raw_message else None) or observation.device_id,
    }


def _latest_previous_final(
    session: Session,
    context: dict[str, Any],
) -> ObservationRecord | None:
    observation: ObservationRecord = context["observation"]
    stmt = (
        select(ObservationRecord)
        .join(OrderItemRecord, ObservationRecord.order_item_id == OrderItemRecord.id)
        .join(OrderRecord, OrderItemRecord.order_id == OrderRecord.id)
        .where(OrderRecord.patient_id == context["patient_id"])
        .where(ObservationRecord.code_local == observation.code_local)
        .where(ObservationRecord.id != observation.id)
        .where(ObservationRecord.status.in_(["final", "corrected", "amended"]))
        .order_by(
            func.coalesce(
                ObservationRecord.issued_at,
                ObservationRecord.effective_at,
                ObservationRecord.created_at,
            ).desc()
        )
    )
    return session.scalar(stmt)


def _list_applicable_rules(
    session: Session,
    context: dict[str, Any],
) -> list[AutoverificationRuleRecord]:
    stmt = (
        select(AutoverificationRuleRecord)
        .where(AutoverificationRuleRecord.active.is_(True))
        .order_by(
            AutoverificationRuleRecord.priority.asc(),
            AutoverificationRuleRecord.created_at.asc(),
        )
    )
    test_catalog_id = context["test_catalog_id"]
    device_id = context["source_device_id"]
    specimen_type_code = context["specimen_type_code"]
    stmt = stmt.where(
        (AutoverificationRuleRecord.test_catalog_id.is_(None))
        | (AutoverificationRuleRecord.test_catalog_id == test_catalog_id)
    )
    stmt = stmt.where(
        (AutoverificationRuleRecord.device_id.is_(None))
        | (AutoverificationRuleRecord.device_id == device_id)
    )
    stmt = stmt.where(
        (AutoverificationRuleRecord.specimen_type_code.is_(None))
        | (AutoverificationRuleRecord.specimen_type_code == specimen_type_code)
    )
    return session.scalars(stmt).all()


def _evaluate_rule(
    rule: AutoverificationRuleRecord,
    context: dict[str, Any],
    previous_final: ObservationRecord | None,
) -> AutoverificationRuleEvaluation:
    observation: ObservationRecord = context["observation"]
    condition = rule.condition_payload or {}
    reasons: list[str] = []

    if condition.get("require_value", True):
        if observation.value_type == "quantity" and observation.value_num is None:
            reasons.append("quantity value is missing")
        elif observation.value_type in {"text", "attachment"} and not observation.value_text:
            reasons.append(f"{observation.value_type} value is missing")
        elif observation.value_type == "coded" and not observation.value_code:
            reasons.append("coded value is missing")
        elif observation.value_type == "boolean" and observation.value_boolean is None:
            reasons.append("boolean value is missing")

    specimen_status_in = condition.get("specimen_status_in")
    if specimen_status_in and context["specimen_status"] not in specimen_status_in:
        reasons.append(f"specimen status {context['specimen_status']!r} not allowed")

    unit_ucum_equals = condition.get("unit_ucum_equals")
    if unit_ucum_equals and observation.unit_ucum != unit_ucum_equals:
        reasons.append(
            f"unit {observation.unit_ucum!r} does not match required {unit_ucum_equals!r}"
        )

    allowed_flags = condition.get("allowed_abnormal_flags")
    if allowed_flags is not None and (observation.abnormal_flag or "") not in allowed_flags:
        reasons.append(f"abnormal flag {(observation.abnormal_flag or '')!r} not in allowed set")

    disallowed_flags = condition.get("disallow_abnormal_flags")
    if disallowed_flags and (observation.abnormal_flag or "") in disallowed_flags:
        reasons.append(f"abnormal flag {(observation.abnormal_flag or '')!r} is disallowed")

    _check_numeric_limit(reasons, "minimum", observation.value_num, condition.get("numeric_min"), below=True)
    _check_numeric_limit(reasons, "maximum", observation.value_num, condition.get("numeric_max"), below=False)
    _check_critical_limit(reasons, observation.value_num, condition.get("critical_low"), is_low=True)
    _check_critical_limit(reasons, observation.value_num, condition.get("critical_high"), is_low=False)

    if condition.get("require_previous_final") and previous_final is None:
        reasons.append("previous final result required for delta check but not found")

    if previous_final is not None and observation.value_num is not None and previous_final.value_num is not None:
        delta = abs(float(observation.value_num) - float(previous_final.value_num))
        delta_abs_max = condition.get("delta_abs_max")
        if delta_abs_max is not None and delta > float(delta_abs_max):
            reasons.append(f"absolute delta {delta:.4f} exceeds max {delta_abs_max}")
        delta_percent_max = condition.get("delta_percent_max")
        if delta_percent_max is not None:
            previous_abs = abs(float(previous_final.value_num))
            delta_percent = 0.0 if previous_abs == 0 and delta == 0 else (
                999999.0 if previous_abs == 0 else (delta / previous_abs) * 100.0
            )
            if delta_percent > float(delta_percent_max):
                reasons.append(f"percent delta {delta_percent:.2f}% exceeds max {delta_percent_max}%")

    return AutoverificationRuleEvaluation(
        rule_id=rule.id,
        rule_name=rule.name,
        priority=rule.priority,
        decision=AutoverificationCheckDecision.PASS
        if not reasons
        else AutoverificationCheckDecision.FAIL,
        reasons=reasons,
        condition=condition,
    )


def _check_numeric_limit(
    reasons: list[str],
    label: str,
    value_num: float | None,
    threshold: Any,
    *,
    below: bool,
) -> None:
    if threshold is None:
        return
    if value_num is None:
        reasons.append(f"numeric {label} cannot be checked without numeric value")
        return
    threshold_value = float(threshold)
    if below and float(value_num) < threshold_value:
        reasons.append(f"value {value_num} below minimum {threshold}")
    if not below and float(value_num) > threshold_value:
        reasons.append(f"value {value_num} above maximum {threshold}")


def _check_critical_limit(
    reasons: list[str],
    value_num: float | None,
    threshold: Any,
    *,
    is_low: bool,
) -> None:
    if threshold is None or value_num is None:
        return
    threshold_value = float(threshold)
    if is_low and float(value_num) <= threshold_value:
        reasons.append(f"value {value_num} reached critical low threshold {threshold}")
    if not is_low and float(value_num) >= threshold_value:
        reasons.append(f"value {value_num} reached critical high threshold {threshold}")


def _ensure_review_task(
    session: Session,
    *,
    observation: ObservationRecord,
    order_item: OrderItemRecord,
    device_id: str | None,
    reasons: list[str],
) -> TaskRecord:
    existing = session.scalar(
        select(TaskRecord)
        .where(TaskRecord.focus_type == "observation")
        .where(TaskRecord.focus_id == observation.id)
        .where(TaskRecord.queue_code == "manual-review")
        .where(TaskRecord.status.in_(ALLOWED_REVIEW_TASK_STATUSES))
        .order_by(TaskRecord.authored_on.desc())
    )
    if existing is not None:
        return existing
    task = TaskRecord(
        id=str(uuid4()),
        based_on_order_item_id=order_item.id,
        focus_type="observation",
        focus_id=observation.id,
        queue_code="manual-review",
        status="ready",
        business_status="autoverification-hold",
        device_id=device_id,
        inputs_payload={"reasons": reasons, "observation_id": observation.id},
    )
    session.add(task)
    return task


def _persist_run_rows(
    session: Session,
    *,
    observation_id: str,
    evaluation: AutoverificationEvaluateResponse,
    decision: AutoverificationApplyDecision,
    created_task_id: str | None,
) -> None:
    for item in evaluation.rules:
        session.add(
            AutoverificationRunRecord(
                id=str(uuid4()),
                observation_id=observation_id,
                rule_id=str(item.rule_id),
                decision=item.decision.value,
                reasons_payload=item.reasons,
                evaluated_at=datetime.now(UTC),
            )
        )
    summary_reasons = list(evaluation.implicit_reasons)
    for item in evaluation.rules:
        summary_reasons.extend(item.reasons)
    session.add(
        AutoverificationRunRecord(
            id=str(uuid4()),
            observation_id=observation_id,
            rule_id=None,
            decision=decision.value,
            reasons_payload=summary_reasons,
            evaluated_at=datetime.now(UTC),
            created_task_id=created_task_id,
        )
    )


def _to_rule_summary(rule: AutoverificationRuleRecord) -> AutoverificationRuleSummary:
    return AutoverificationRuleSummary(
        id=rule.id,
        name=rule.name,
        active=rule.active,
        priority=rule.priority,
        test_catalog_id=rule.test_catalog_id,
        device_id=rule.device_id,
        specimen_type_code=rule.specimen_type_code,
        rule_type=rule.rule_type,
        condition=rule.condition_payload,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def _to_run_summary(run: AutoverificationRunRecord) -> AutoverificationRunSummary:
    return AutoverificationRunSummary(
        id=run.id,
        observation_id=run.observation_id,
        rule_id=run.rule_id,
        decision=run.decision,
        reasons=run.reasons_payload,
        evaluated_at=run.evaluated_at,
        created_task_id=run.created_task_id,
    )


def _optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None
