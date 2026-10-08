from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.products.dtos import ProductResponse


class ReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, max_length=5000)


class ReviewUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("At least one review field must be provided")
        return self


class WishlistAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(ge=1)


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    reviewer_name: str
    rating: int
    title: str | None
    body: str | None
    created_at: datetime
    updated_at: datetime


class WishlistItemResponse(BaseModel):
    id: int
    product_id: int
    product: ProductResponse
    created_at: datetime


class WishlistResponse(BaseModel):
    items: list[WishlistItemResponse]
