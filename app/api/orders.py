from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.helpers import raise_not_implemented
from app.schemas.common import ApiError
from app.schemas.orders import (
    CreateOrderRequest,
    OrderDetail,
    OrderItemActionRequest,
    OrderItemCreateRequest,
    OrderItemSummary,
    OrderSummary,
)

router = APIRouter(prefix="/api/v1", tags=["orders"])
NOT_IMPLEMENTED = {
    status.HTTP_501_NOT_IMPLEMENTED: {
        "model": ApiError,
        "description": "Route exists, but workflow logic is not implemented yet.",
    }
}


@router.post(
    "/orders",
    response_model=OrderSummary,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_IMPLEMENTED,
)
def create_order(payload: CreateOrderRequest) -> OrderSummary:
    del payload
    raise_not_implemented("Order creation")


@router.get("/orders", response_model=dict[str, list[OrderSummary]], responses=NOT_IMPLEMENTED)
def list_orders(
    requisition_no: str | None = None,
    patient_id: UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> dict[str, list[OrderSummary]]:
    del requisition_no, patient_id, status_filter
    raise_not_implemented("Order search")


@router.get("/orders/{order_id}", response_model=OrderDetail, responses=NOT_IMPLEMENTED)
def get_order(order_id: UUID) -> OrderDetail:
    del order_id
    raise_not_implemented("Order read")


@router.post(
    "/orders/{order_id}/items",
    response_model=OrderItemSummary,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_IMPLEMENTED,
)
def create_order_item(order_id: UUID, payload: OrderItemCreateRequest) -> OrderItemSummary:
    del order_id, payload
    raise_not_implemented("Order item creation")


@router.post(
    "/order-items/{order_item_id}/cancel",
    response_model=OrderItemSummary,
    responses=NOT_IMPLEMENTED,
)
def cancel_order_item(order_item_id: UUID, payload: OrderItemActionRequest) -> OrderItemSummary:
    del order_item_id, payload
    raise_not_implemented("Order item cancellation")


@router.post(
    "/order-items/{order_item_id}/hold",
    response_model=OrderItemSummary,
    responses=NOT_IMPLEMENTED,
)
def hold_order_item(order_item_id: UUID, payload: OrderItemActionRequest) -> OrderItemSummary:
    del order_item_id, payload
    raise_not_implemented("Order item hold")

