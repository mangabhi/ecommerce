from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.inventory import controller
from src.inventory.dtos import (
    InventoryAdjustmentRequest,
    InventoryAdjustmentResponse,
    InventoryResponse,
)
from src.utils.db import get_db
from src.utils.helpers import is_admin

inventory_routes = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


@inventory_routes.get("/low-stock", response_model=list[InventoryResponse])
def list_low_stock(
    threshold: int = Query(default=10, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.list_low_stock(threshold, limit, db)


@inventory_routes.get("/{product_id}", response_model=InventoryResponse)
def get_inventory(product_id: int, db: Session = Depends(get_db)):
    return controller.get_inventory(product_id, db)


@inventory_routes.patch(
    "/{product_id}",
    response_model=InventoryAdjustmentResponse,
)
def adjust_inventory(
    product_id: int,
    body: InventoryAdjustmentRequest,
    admin: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.adjust_inventory(product_id, body, admin.id, db)
