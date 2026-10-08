from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.orders import controller
from src.orders.dtos import (
    OrderCancellationRequest,
    OrderCreateRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
)
from src.utils.db import get_db
from src.utils.helpers import is_admin, is_authenticated

order_routes = APIRouter(prefix="/api/v1/orders", tags=["orders"])
checkout_routes = APIRouter(prefix="/api/v1/checkout", tags=["checkout"])
admin_order_routes = APIRouter(prefix="/api/v1/admin/orders", tags=["orders"])


@checkout_routes.post("", response_model=OrderResponse, status_code=201)
def checkout(
    body: OrderCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.create_order(current_user.id, body, db)


@order_routes.post("", response_model=OrderResponse, status_code=201)
def create_order(
    body: OrderCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.create_order(current_user.id, body, db)


@order_routes.get("", response_model=list[OrderResponse])
def list_orders(
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.list_orders(current_user.id, db)


@admin_order_routes.get("", response_model=list[OrderResponse])
def list_all_orders(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.list_all_orders(limit, offset, db)


@admin_order_routes.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    body: OrderStatusUpdateRequest,
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.update_order_status(order_id, body, db)


@order_routes.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.get_order(order_id, current_user.id, db)


@order_routes.post("/{order_id}/cancel", response_model=OrderResponse)
def request_cancellation(
    order_id: int,
    body: OrderCancellationRequest = OrderCancellationRequest(),
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.request_cancellation(
        order_id,
        current_user.id,
        body.reason,
        db,
    )


@order_routes.get("/{order_id}/tracking")
def get_tracking(
    order_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.get_tracking(order_id, current_user.id, db)
