from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.coupons.dtos import CouponCreateRequest, CouponUpdateRequest
from src.coupons.models import Coupon

CENT = Decimal("0.01")


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def validate_coupon(code: str, subtotal: Decimal, db: Session) -> tuple[Coupon, Decimal]:
    now = datetime.now(timezone.utc)
    coupon = (
        db.query(Coupon)
        .filter(Coupon.code == code.strip().upper())
        .first()
    )
    if coupon is None or not coupon.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is unavailable")
    if _utc(coupon.starts_at) is not None and _utc(coupon.starts_at) > now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon is not active yet")
    if _utc(coupon.expires_at) is not None and _utc(coupon.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon has expired")
    if subtotal < coupon.minimum_order_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order subtotal does not meet the coupon minimum",
        )
    if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit reached")

    if coupon.discount_type == "percentage":
        discount = (subtotal * coupon.discount_value / Decimal("100")).quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )
        if coupon.maximum_discount is not None:
            discount = min(discount, coupon.maximum_discount)
    else:
        discount = coupon.discount_value
    return coupon, min(discount, subtotal)


def create_coupon(body: CouponCreateRequest, db: Session) -> Coupon:
    values = body.model_dump()
    values["code"] = values["code"].strip().upper()
    existing = db.query(Coupon.id).filter(Coupon.code == values["code"]).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Coupon code already exists")
    coupon = Coupon(**values)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(coupon_id: int, body: CouponUpdateRequest, db: Session) -> Coupon:
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if coupon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    changes = body.model_dump(exclude_unset=True)
    discount_type = changes.get("discount_type", coupon.discount_type)
    discount_value = changes.get("discount_value", coupon.discount_value)
    starts_at = changes.get("starts_at", coupon.starts_at)
    expires_at = changes.get("expires_at", coupon.expires_at)
    if discount_value is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="discount_value cannot be null",
        )
    if discount_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="discount_type cannot be null",
        )
    if discount_type == "percentage" and discount_value > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Percentage discount cannot exceed 100",
        )
    if starts_at and expires_at and _utc(expires_at) <= _utc(starts_at):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="expires_at must be after starts_at",
        )
    for field, value in changes.items():
        setattr(coupon, field, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def list_coupons(db: Session) -> list[Coupon]:
    return db.query(Coupon).order_by(Coupon.created_at.desc(), Coupon.id.desc()).all()


def quote(subtotal: Decimal, code: str | None, db: Session) -> dict:
    if code is None:
        return {
            "subtotal": subtotal,
            "discount_amount": Decimal("0.00"),
            "total": subtotal,
            "coupon_code": None,
        }
    coupon, discount = validate_coupon(code, subtotal, db)
    return {
        "subtotal": subtotal,
        "discount_amount": discount,
        "total": subtotal - discount,
        "coupon_code": coupon.code,
    }
