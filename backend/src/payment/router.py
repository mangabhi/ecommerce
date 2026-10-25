import hmac

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.payment import controller
from src.payment.dtos import (
    PaymentCreateRequest,
    PaymentIntentResponse,
    PaymentRefundRequest,
    PaymentResponse,
    PaymentWebhookRequest,
)
from src.utils.db import get_db
from src.utils.helpers import is_admin, is_authenticated
from src.utils.settings import settings

payment_routes = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@payment_routes.get("/config")
def get_payment_config():
    return controller.get_stripe_config()


@payment_routes.post(
    "/create",
    response_model=PaymentIntentResponse,
    status_code=201,
)
def create_payment(
    body: PaymentCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    payment, client_secret = controller.create_payment(current_user.id, body, db)
    return {
        **PaymentResponse.model_validate(payment).model_dump(),
        "client_secret": client_secret,
    }


@payment_routes.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook signing secret is not configured",
        )
    if stripe_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook signature or payload",
        ) from error
    controller.process_stripe_event(
        event.type,
        event.data.object,
        db,
    )
    return {"received": True}


@payment_routes.post("/webhook", response_model=PaymentResponse)
def payment_webhook(
    body: PaymentWebhookRequest,
    x_mock_webhook_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if settings.APP_ENV.lower() != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    configured_secret = settings.MOCK_PAYMENT_WEBHOOK_SECRET
    if not configured_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mock payment webhook secret is not configured",
        )
    if x_mock_webhook_secret is None or not hmac.compare_digest(
        x_mock_webhook_secret,
        configured_secret,
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")
    return controller.process_mock_webhook(
        body.provider_reference,
        body.status,
        body.amount,
        db,
    )


@payment_routes.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.get_payment(
        payment_id,
        current_user.id,
        current_user.role == "admin",
        db,
    )


@payment_routes.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.confirm_stripe_payment(payment_id, current_user.id, db)


@payment_routes.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    body: PaymentRefundRequest = PaymentRefundRequest(),
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.refund_payment(
        payment_id,
        current_user.id,
        current_user.role == "admin",
        body.reason,
        db,
    )
