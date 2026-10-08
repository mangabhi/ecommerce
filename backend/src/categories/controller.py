from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.categories.models import Category
from src.products.models import Product


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.name.asc(), Category.id.asc()).all()


def list_category_products(category_id: int, db: Session) -> list[Product]:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return (
        db.query(Product)
        .filter(
            Product.category_id == category_id,
            Product.is_active.is_(True),
        )
        .order_by(Product.name.asc(), Product.id.asc())
        .all()
    )
