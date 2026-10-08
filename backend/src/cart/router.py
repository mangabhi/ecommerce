from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.cart import controller
from src.cart.dtos import CartItemCreateRequest, CartItemUpdateRequest, CartResponse
from src.utils.db import get_db
from src.utils.helpers import is_authenticated

cart_routes = APIRouter(prefix="/api/v1/cart", tags=["cart"])


@cart_routes.get("", response_model=CartResponse)
def get_cart(
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.get_cart(current_user.id, db)


@cart_routes.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_cart_item(
    body: CartItemCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.add_item(current_user.id, body.product_id, body.quantity, db)


@cart_routes.patch("/items/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: int,
    body: CartItemUpdateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.update_item(current_user.id, item_id, body.quantity, db)


@cart_routes.delete("/items/{item_id}", response_model=CartResponse)
def remove_cart_item(
    item_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.remove_item(current_user.id, item_id, db)


@cart_routes.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    controller.clear_cart(current_user.id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
