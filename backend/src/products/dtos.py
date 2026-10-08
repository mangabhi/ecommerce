from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: Optional[int] = Field(default=None, ge=1)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=2048)


class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: Optional[int] = Field(default=None, ge=1)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[str] = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("At least one product field must be provided")
        for field_name in {
            "name",
            "price",
            "stock_quantity",
        } & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: Optional[int]
    name: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
