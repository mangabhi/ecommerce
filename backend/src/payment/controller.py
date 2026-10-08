import secrets
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.notifications.models import Notification
from src.coupons.models import Coupon, CouponRedemption
from src.orders.models import Order
from src.payment.dtos import PaymentCreateRequest
from src.payment.models import Payment
from src.products.models import Product
from sqlalchemy import update


def create_payment(user_id: int, body: PaymentCreateRequest, db: Session) -> Payment:
    order = (
        db.query(Order)
        .filter(Order.id == body.order_id, Order.user_id == user_id)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "pending_payment":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order is not awaiting payment",
        )
    existing = (
        db.query(Payment)
        .filter(Payment.order_id == order.id, Payment.status == "pending")
        .first()
    )
    if existing is not None:
        return existing
    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        provider="mock",
        provider_reference=secrets.token_urlsafe(24),
        status="pending",
        amount=order.total,
        currency=body.currency,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment(payment_id: int, user_id: int, is_admin: bool, db: Session) -> Payment:
    query = db.query(Payment).filter(Payment.id == payment_id)
    if not is_admin:
        query = query.filter(Payment.user_id == user_id)
    payment = query.first()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


def process_mock_webhook(
    provider_reference: str,
    payment_status: str,
    amount: Decimal,
    db: Session,
) -> Payment:
    payment = (
        db.query(Payment)
        .filter(Payment.provider_reference == provider_reference)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.amount != amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount does not match",
        )
    if payment.status != "pending":
        if payment.status == payment_status:
            return payment
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment is already {payment.status}",
        )
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "pending_payment":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order is no longer awaiting payment",
        )
    payment.status = payment_status
    if payment_status == "succeeded":
        order.status = "paid"
        title = "Payment received"
        message = f"Payment for order #{order.id} was successful."
    else:
        order.status = "payment_failed"
        for item in order.items:
            if item.product_id is not None:
                db.execute(
                    update(Product)
                    .where(Product.id == item.product_id)
                    .values(stock_quantity=Product.stock_quantity + item.quantity)
                )
        title = "Payment failed"
        message = f"Payment for order #{order.id} failed."
        if order.coupon_code is not None:
            coupon = db.query(Coupon).filter(Coupon.code == order.coupon_code).first()
            if coupon is not None:
                db.execute(
                    update(Coupon)
                    .where(Coupon.id == coupon.id, Coupon.usage_count > 0)
                    .values(usage_count=Coupon.usage_count - 1)
                )
            db.query(CouponRedemption).filter(
                CouponRedemption.order_id == order.id
            ).delete()
    db.add(Notification(user_id=payment.user_id, title=title, message=message))
    db.commit()
    db.refresh(payment)
    return payment


def refund_payment(
    payment_id: int,
    user_id: int,
    is_admin: bool,
    reason: str | None,
    db: Session,
) -> Payment:
    query = db.query(Payment).filter(Payment.id == payment_id)
    if not is_admin:
        query = query.filter(Payment.user_id == user_id)
    payment = query.first()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status == "refunded":
        return payment
    if payment.status != "succeeded":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only successful payments can be refunded",
        )
    payment.status = "refunded"
    payment.refund_reason = reason
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order is not None:
        order.status = "refunded"
        db.add(
            Notification(
                user_id=payment.user_id,
                title="Payment refunded",
                message=f"Payment for order #{order.id} was refunded.",
            )
        )
    db.commit()
    db.refresh(payment)
    return payment
