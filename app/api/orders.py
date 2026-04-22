from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, require_roles
from app.schemas.auth import RoleCode, UserSummary
from app.schemas.orders import (
    CreateOrderRequest,
    OrderDetail,
    OrderItemActionRequest,
    OrderItemCreateRequest,
    OrderItemSummary,
    OrderSummary,
)
from app.services import orders as order_service

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.post(
    "/orders",
    response_model=OrderSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: CreateOrderRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER)),
) -> OrderSummary:
    return order_service.create_order(session, payload, actor=current_user)


@router.get("/orders", response_model=dict[str, list[OrderSummary]])
def list_orders(
    session: DbSession,
    requisition_no: str | None = None,
    patient_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: UserSummary = Depends(
        require_roles(
            RoleCode.ADMIN,
            RoleCode.ACCESSIONER,
            RoleCode.TECHNICIAN,
            RoleCode.PATHOLOGIST,
            RoleCode.VIEWER,
        )
    ),
) -> dict[str, list[OrderSummary]]:
    return {
        "items": order_service.list_orders(
            session,
            requisition_no=requisition_no,
            patient_id=patient_id,
            status_filter=status_filter,
        )
    }


@router.get("/orders/{order_id}", response_model=OrderDetail)
def get_order(
    order_id: UUID,
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
) -> OrderDetail:
    return order_service.get_order(session, order_id)


@router.post(
    "/orders/{order_id}/items",
    response_model=OrderItemSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_order_item(
    order_id: UUID,
    payload: OrderItemCreateRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER)),
) -> OrderItemSummary:
    return order_service.create_order_item(session, order_id, payload, actor=current_user)


@router.post(
    "/order-items/{order_item_id}/cancel",
    response_model=OrderItemSummary,
)
def cancel_order_item(
    order_item_id: UUID,
    payload: OrderItemActionRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER)),
) -> OrderItemSummary:
    return order_service.cancel_order_item(session, order_item_id, payload, actor=current_user)


@router.post(
    "/order-items/{order_item_id}/hold",
    response_model=OrderItemSummary,
)
def hold_order_item(
    order_item_id: UUID,
    payload: OrderItemActionRequest,
    session: DbSession,
    current_user: UserSummary = Depends(require_roles(RoleCode.ADMIN, RoleCode.ACCESSIONER)),
) -> OrderItemSummary:
    return order_service.hold_order_item(session, order_item_id, payload, actor=current_user)
