from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.cart.models import Cart, CartItem
from src.auth.models import AuthUser
from src.coupons import controller
from src.coupons.dtos import (
    CouponCreateRequest,
    CouponQuoteRequest,
    CouponQuoteResponse,
    CouponResponse,
    CouponUpdateRequest,
    CouponValidationRequest,
)
from src.products.models import Product
from src.utils.db import get_db
from src.utils.helpers import is_admin, is_authenticated

coupon_routes = APIRouter(prefix="/api/v1/coupons", tags=["coupons"])
checkout_quote_routes = APIRouter(prefix="/api/v1/checkout", tags=["checkout"])
admin_coupon_routes = APIRouter(prefix="/api/v1/admin/coupons", tags=["coupons"])


@coupon_routes.post("/validate", response_model=CouponQuoteResponse)
def validate_coupon(
    body: CouponValidationRequest,
    db: Session = Depends(get_db),
):
    coupon, discount = controller.validate_coupon(body.code, body.subtotal, db)
    return {
        "subtotal": body.subtotal,
        "discount_amount": discount,
        "total": body.subtotal - discount,
        "coupon_code": coupon.code,
    }


@admin_coupon_routes.post("", response_model=CouponResponse, status_code=201)
def create_coupon(
    body: CouponCreateRequest,
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.create_coupon(body, db)


@admin_coupon_routes.patch("/{coupon_id}", response_model=CouponResponse)
def update_coupon(
    coupon_id: int,
    body: CouponUpdateRequest,
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.update_coupon(coupon_id, body, db)


@admin_coupon_routes.get("", response_model=list[CouponResponse])
def list_coupons(
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.list_coupons(db)


@checkout_quote_routes.post("/quote", response_model=CouponQuoteResponse)
def checkout_quote(
    body: CouponQuoteRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .first()
    )
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    cart_items = (
        db.query(CartItem, Product)
        .join(Product, Product.id == CartItem.product_id)
        .filter(CartItem.cart_id == cart.id, Product.is_active.is_(True))
        .all()
    )
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    subtotal = sum(
        (Decimal(product.price) * item.quantity for item, product in cart_items),
        start=Decimal("0.00"),
    )
    return controller.quote(subtotal, body.code, db)
