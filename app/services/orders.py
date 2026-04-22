from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import OrderItemRecord, OrderRecord, PatientRecord, TestCatalogRecord
from app.schemas.auth import UserSummary
from app.schemas.orders import (
    CreateOrderRequest,
    OrderDetail,
    OrderItemActionRequest,
    OrderItemCreateRequest,
    OrderItemSummary,
    OrderSummary,
)
from app.services.audit import write_audit_event

ACTIVE_ORDER_ITEM_STATUSES = {"registered", "on_hold"}
TERMINAL_ORDER_ITEM_STATUSES = {"cancelled"}


def create_order(
    session: Session,
    payload: CreateOrderRequest,
    *,
    actor: UserSummary | None = None,
) -> OrderSummary:
    _ensure_patient_exists(session, payload.patient_id)

    order = OrderRecord(
        id=str(uuid4()),
        requisition_no=_generate_identifier("REQ"),
        patient_id=str(payload.patient_id),
        encounter_case_id=_optional_uuid(payload.encounter_case_id),
        source_system=payload.source_system,
        placer_order_no=payload.placer_order_no,
        priority=payload.priority.value,
        status="registered",
        clinical_info=payload.clinical_info,
        requested_by_practitioner_role_id=_optional_uuid(payload.requested_by_practitioner_role_id),
        ordered_at=payload.ordered_at,
        order_metadata=payload.metadata,
    )
    session.add(order)

    for line_no, item_payload in enumerate(payload.items, start=1):
        _ensure_test_catalog_exists(session, item_payload.test_catalog_id)
        session.add(
            OrderItemRecord(
                id=str(uuid4()),
                order=order,
                line_no=line_no,
                test_catalog_id=str(item_payload.test_catalog_id),
                requested_specimen_type_code=item_payload.requested_specimen_type_code,
                status="registered",
                priority=(item_payload.priority or payload.priority).value,
                reflex_policy_code=item_payload.reflex_policy_code,
                aoe_payload=item_payload.aoe_payload,
            )
        )

    write_audit_event(
        session,
        entity_type="order",
        entity_id=order.id,
        action="create",
        status=order.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"item_count": len(payload.items), "source_system": payload.source_system},
    )
    session.commit()
    session.refresh(order)
    return _to_order_summary(order)


def list_orders(
    session: Session,
    *,
    requisition_no: str | None = None,
    patient_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[OrderSummary]:
    stmt: Select[tuple[OrderRecord]] = select(OrderRecord).order_by(OrderRecord.ordered_at.desc())
    if requisition_no:
        stmt = stmt.where(OrderRecord.requisition_no == requisition_no)
    if patient_id:
        stmt = stmt.where(OrderRecord.patient_id == str(patient_id))
    if status_filter:
        stmt = stmt.where(OrderRecord.status == status_filter)
    return [_to_order_summary(row) for row in session.scalars(stmt).all()]


def get_order(session: Session, order_id: UUID) -> OrderDetail:
    order = _get_order_or_404(session, order_id, with_items=True)
    return _to_order_detail(order)


def create_order_item(
    session: Session,
    order_id: UUID,
    payload: OrderItemCreateRequest,
    *,
    actor: UserSummary | None = None,
) -> OrderItemSummary:
    order = _get_order_or_404(session, order_id, with_items=True)
    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot add items to a cancelled order.",
        )

    _ensure_test_catalog_exists(session, payload.test_catalog_id)
    line_no = max((item.line_no for item in order.items), default=0) + 1
    item = OrderItemRecord(
        id=str(uuid4()),
        order=order,
        line_no=line_no,
        test_catalog_id=str(payload.test_catalog_id),
        requested_specimen_type_code=payload.requested_specimen_type_code,
        status="registered",
        priority=payload.priority.value if payload.priority else order.priority,
        reflex_policy_code=payload.reflex_policy_code,
        aoe_payload=payload.aoe_payload,
    )
    session.add(item)
    order.status = "registered"
    order.cancelled_at = None

    write_audit_event(
        session,
        entity_type="order-item",
        entity_id=item.id,
        action="create",
        status=item.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"order_id": order.id, "line_no": line_no},
    )
    write_audit_event(
        session,
        entity_type="order",
        entity_id=order.id,
        action="append-item",
        status=order.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"order_item_id": item.id},
    )
    session.commit()
    session.refresh(item)
    return _to_order_item_summary(item)


def cancel_order_item(
    session: Session,
    order_item_id: UUID,
    payload: OrderItemActionRequest,
    *,
    actor: UserSummary | None = None,
) -> OrderItemSummary:
    item = _get_order_item_or_404(session, order_item_id)
    if item.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order item is already cancelled.",
        )

    item.status = "cancelled"
    _synchronize_order_status(item.order)
    write_audit_event(
        session,
        entity_type="order-item",
        entity_id=item.id,
        action="cancel",
        status=item.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    write_audit_event(
        session,
        entity_type="order",
        entity_id=item.order.id,
        action="recalculate-status",
        status=item.order.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"trigger": "item-cancelled", "order_item_id": item.id},
    )
    session.commit()
    session.refresh(item)
    return _to_order_item_summary(item)


def hold_order_item(
    session: Session,
    order_item_id: UUID,
    payload: OrderItemActionRequest,
    *,
    actor: UserSummary | None = None,
) -> OrderItemSummary:
    item = _get_order_item_or_404(session, order_item_id)
    if item.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cancelled order items cannot be placed on hold.",
        )

    item.status = "on_hold"
    _synchronize_order_status(item.order)
    write_audit_event(
        session,
        entity_type="order-item",
        entity_id=item.id,
        action="hold",
        status=item.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"reason": payload.reason, "comment": payload.comment},
    )
    write_audit_event(
        session,
        entity_type="order",
        entity_id=item.order.id,
        action="recalculate-status",
        status=item.order.status,
        actor_user_id=str(actor.id) if actor else None,
        actor_username=actor.username if actor else None,
        actor_role_code=actor.role_code.value if actor else None,
        context={"trigger": "item-held", "order_item_id": item.id},
    )
    session.commit()
    session.refresh(item)
    return _to_order_item_summary(item)


def _get_order_or_404(session: Session, order_id: UUID, *, with_items: bool = False) -> OrderRecord:
    stmt = select(OrderRecord).where(OrderRecord.id == str(order_id))
    if with_items:
        stmt = stmt.options(selectinload(OrderRecord.items))
    order = session.scalar(stmt)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} was not found.",
        )
    return order


def _get_order_item_or_404(session: Session, order_item_id: UUID) -> OrderItemRecord:
    stmt = (
        select(OrderItemRecord)
        .options(selectinload(OrderItemRecord.order).selectinload(OrderRecord.items))
        .where(OrderItemRecord.id == str(order_item_id))
    )
    item = session.scalar(stmt)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order item {order_item_id} was not found.",
        )
    return item


def _synchronize_order_status(order: OrderRecord) -> None:
    item_statuses = {item.status for item in order.items}
    if item_statuses and item_statuses.issubset(TERMINAL_ORDER_ITEM_STATUSES):
        order.status = "cancelled"
        order.cancelled_at = datetime.now(UTC)
        return
    if "on_hold" in item_statuses:
        order.status = "on_hold"
        order.cancelled_at = None
        return
    if item_statuses & ACTIVE_ORDER_ITEM_STATUSES:
        order.status = "registered"
        order.cancelled_at = None


def _generate_identifier(prefix: str) -> str:
    return f"{prefix}-{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid4().hex[:8].upper()}"


def _ensure_patient_exists(session: Session, patient_id: UUID) -> None:
    patient = session.get(PatientRecord, str(patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} was not found.",
        )


def _ensure_test_catalog_exists(session: Session, test_catalog_id: UUID) -> None:
    item = session.get(TestCatalogRecord, str(test_catalog_id))
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catalog item {test_catalog_id} was not found.",
        )


def _optional_uuid(value: UUID | None) -> str | None:
    return str(value) if value else None


def _to_order_summary(order: OrderRecord) -> OrderSummary:
    return OrderSummary(
        id=order.id,
        requisition_no=order.requisition_no,
        patient_id=order.patient_id,
        source_system=order.source_system,
        priority=order.priority,
        status=order.status,
        ordered_at=order.ordered_at,
    )


def _to_order_item_summary(item: OrderItemRecord) -> OrderItemSummary:
    return OrderItemSummary(
        id=item.id,
        order_id=item.order_id,
        line_no=item.line_no,
        test_catalog_id=item.test_catalog_id,
        requested_specimen_type_code=item.requested_specimen_type_code,
        status=item.status,
        priority=item.priority,
    )


def _to_order_detail(order: OrderRecord) -> OrderDetail:
    return OrderDetail(
        **_to_order_summary(order).model_dump(),
        encounter_case_id=order.encounter_case_id,
        clinical_info=order.clinical_info,
        items=[_to_order_item_summary(item) for item in order.items],
    )
