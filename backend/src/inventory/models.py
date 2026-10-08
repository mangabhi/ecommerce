from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from src.utils.db import Base


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustment"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    adjusted_by = Column(Integer, ForeignKey("auth_user.id", ondelete="SET NULL"), nullable=True)
    change = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
