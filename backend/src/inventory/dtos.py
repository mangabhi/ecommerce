from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InventoryAdjustmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change: int = Field(ne=0, ge=-1000000, le=1000000)
    reason: str | None = Field(default=None, max_length=1000)


class InventoryResponse(BaseModel):
    product_id: int
    product_name: str
    stock_quantity: int


class InventoryAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    adjusted_by: int | None
    change: int
    stock_after: int
    reason: str | None
    created_at: datetime
