import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.payment import controller
from src.payment.dtos import (
    PaymentCreateRequest,
    PaymentRefundRequest,
    PaymentResponse,
    PaymentWebhookRequest,
)
from src.utils.db import get_db
from src.utils.helpers import is_admin, is_authenticated
from src.utils.settings import settings

payment_routes = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@payment_routes.post("/create", response_model=PaymentResponse, status_code=201)
def create_payment(
    body: PaymentCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.create_payment(current_user.id, body, db)


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
