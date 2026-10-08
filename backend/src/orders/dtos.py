from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address_id: int = Field(ge=1)
    coupon_code: str | None = Field(default=None, min_length=1, max_length=64)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int | None
    product_name: str
    unit_price: Decimal
    quantity: int


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    coupon_code: str | None
    shipping_address: dict[str, Any]
    tracking_number: str | None
    tracking_status: str | None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderCancellationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=1000)


class OrderStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(processing|shipped|delivered|cancelled)$")
    tracking_number: str | None = Field(default=None, max_length=100)
    tracking_status: str | None = Field(default=None, max_length=100)
