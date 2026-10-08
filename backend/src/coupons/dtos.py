from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CouponCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64, pattern="^[A-Za-z0-9_-]+$")
    discount_type: Literal["percentage", "fixed"]
    discount_value: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    minimum_order_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    maximum_discount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    usage_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_coupon(self):
        if self.discount_type == "percentage" and self.discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100")
        if self.starts_at and self.expires_at and self.expires_at <= self.starts_at:
            raise ValueError("expires_at must be after starts_at")
        return self


class CouponUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    minimum_order_amount: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    maximum_discount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    usage_limit: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("At least one coupon field must be provided")
        for field_name in {
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "is_active",
        } & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class CouponValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    subtotal: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class CouponQuoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, min_length=1, max_length=64)


class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    discount_type: str
    discount_value: Decimal
    minimum_order_amount: Decimal
    maximum_discount: Decimal | None
    usage_limit: int | None
    usage_count: int
    starts_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CouponQuoteResponse(BaseModel):
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    coupon_code: str | None
