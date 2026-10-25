from decimal import Decimal

from fastapi import HTTPException, status
import stripe
from sqlalchemy.orm import Session

from src.notifications.models import Notification
from src.coupons.models import Coupon, CouponRedemption
from src.orders.models import Order
from src.payment.dtos import PaymentCreateRequest
from src.payment.models import Payment
from src.products.models import Product
from src.utils.settings import settings
from sqlalchemy import update


def _stripe_payment_method_id(intent: stripe.PaymentIntent) -> str | None:
    payment_method = intent.payment_method
    if isinstance(payment_method, str):
        return payment_method
    return getattr(payment_method, "id", None)


def create_payment(
    user_id: int,
    body: PaymentCreateRequest,
    db: Session,
) -> tuple[Payment, str]:
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLISHABLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Add the Stripe test keys to the backend and frontend environment.",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY
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
        if existing.provider != "stripe":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A different payment attempt already exists for this order",
            )
        try:
            intent = stripe.PaymentIntent.retrieve(existing.provider_reference)
        except stripe.StripeError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not retrieve the existing Stripe payment",
            ) from error
        return existing, intent.client_secret

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(Decimal(order.total) * 100),
            currency=body.currency.lower(),
            automatic_payment_methods={"enabled": True},
            metadata={"order_id": str(order.id), "user_id": str(user_id)},
            idempotency_key=f"order-payment-{order.id}",
        )
    except stripe.StripeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe could not start the payment. Please try again.",
        ) from error

    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        provider="stripe",
        provider_reference=intent.id,
        status="pending",
        amount=order.total,
        currency=body.currency,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment, intent.client_secret


def get_stripe_config() -> dict[str, str | bool]:
    return {
        "enabled": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PUBLISHABLE_KEY),
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
    }


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
    return process_payment_status(
        provider_reference,
        payment_status,
        amount,
        None,
        db,
    )


def process_payment_status(
    provider_reference: str,
    payment_status: str,
    amount: Decimal,
    currency: str | None,
    db: Session,
    payment_method_id: str | None = None,
) -> Payment:
    payment = (
        db.query(Payment)
        .filter(Payment.provider_reference == provider_reference)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.amount != amount or (
        currency is not None and payment.currency.lower() != currency.lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount or currency does not match",
        )
    if payment.status != "pending":
        if payment.status == payment_status:
            if payment_method_id and payment.payment_method_id != payment_method_id:
                payment.payment_method_id = payment_method_id
                db.commit()
                db.refresh(payment)
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
    if payment_method_id:
        payment.payment_method_id = payment_method_id
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


def confirm_stripe_payment(
    payment_id: int,
    user_id: int,
    db: Session,
) -> Payment:
    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.user_id == user_id,
            Payment.provider == "stripe",
        )
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status == "succeeded" and payment.payment_method_id:
        return payment
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        intent = stripe.PaymentIntent.retrieve(payment.provider_reference)
    except stripe.StripeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not verify the Stripe payment",
        ) from error
    if intent.status != "succeeded":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stripe has not confirmed this payment",
        )
    return process_payment_status(
        intent.id,
        "succeeded",
        Decimal(intent.amount_received) / 100,
        intent.currency,
        db,
        payment_method_id=_stripe_payment_method_id(intent),
    )


def process_stripe_event(event_type: str, intent: stripe.PaymentIntent, db: Session) -> Payment | None:
    statuses = {
        "payment_intent.succeeded": "succeeded",
        "payment_intent.payment_failed": "failed",
    }
    payment_status = statuses.get(event_type)
    if payment_status is None:
        return None
    amount_minor = (
        intent.amount_received
        if payment_status == "succeeded"
        else intent.amount
    )
    return process_payment_status(
        intent.id,
        payment_status,
        Decimal(amount_minor) / 100,
        intent.currency,
        db,
        payment_method_id=_stripe_payment_method_id(intent),
    )


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
    if payment.provider == "stripe":
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe is not configured",
            )
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe.Refund.create(
                payment_intent=payment.provider_reference,
                reason="requested_by_customer",
                metadata={"reason": reason or ""},
                idempotency_key=f"refund-payment-{payment.id}",
            )
        except stripe.StripeError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Stripe could not process the refund request",
            ) from error
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
