from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: int = Field(ge=1)
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern="^[A-Z]{3}$")


class PaymentWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_reference: str = Field(min_length=1, max_length=128)
    status: Literal["succeeded", "failed"]
    amount: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class PaymentRefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=1000)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    user_id: int
    provider: str
    provider_reference: str
    status: str
    amount: Decimal
    currency: str
    refund_reason: str | None
    created_at: datetime
    updated_at: datetime
