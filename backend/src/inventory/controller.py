from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from src.inventory.dtos import InventoryAdjustmentRequest
from src.inventory.models import InventoryAdjustment
from src.products.models import Product


def get_inventory(product_id: int, db: Session) -> dict:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {
        "product_id": product.id,
        "product_name": product.name,
        "stock_quantity": product.stock_quantity,
    }


def adjust_inventory(
    product_id: int,
    body: InventoryAdjustmentRequest,
    admin_id: int,
    db: Session,
) -> InventoryAdjustment:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    result = db.execute(
        update(Product)
        .where(
            Product.id == product_id,
            Product.stock_quantity + body.change >= 0,
        )
        .values(stock_quantity=Product.stock_quantity + body.change)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock adjustment would make inventory negative",
        )
    db.refresh(product)
    adjustment = InventoryAdjustment(
        product_id=product_id,
        adjusted_by=admin_id,
        change=body.change,
        stock_after=product.stock_quantity,
        reason=body.reason,
    )
    db.add(adjustment)
    db.commit()
    db.refresh(adjustment)
    return adjustment


def list_low_stock(threshold: int, limit: int, db: Session) -> list[dict]:
    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.stock_quantity <= threshold)
        .order_by(Product.stock_quantity.asc(), Product.id.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "product_id": product.id,
            "product_name": product.name,
            "stock_quantity": product.stock_quantity,
        }
        for product in products
    ]
