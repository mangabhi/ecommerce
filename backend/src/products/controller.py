from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.categories.models import Category
from src.products.dtos import ProductCreateRequest, ProductUpdateRequest
from src.products.models import Product


def _validate_category(category_id: int | None, db: Session) -> None:
    if category_id is None:
        return
    if db.query(Category.id).filter(Category.id == category_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


def list_products(
    db: Session,
    *,
    search: str | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
    sort_by: str,
    order: str,
    limit: int,
    offset: int,
) -> list[Product]:
    query = db.query(Product).filter(Product.is_active.is_(True))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            Product.name.ilike(search_term)
            | Product.description.ilike(search_term)
        )
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    sort_columns = {
        "name": Product.name,
        "price": Product.price,
        "created_at": Product.created_at,
    }
    sort_column = sort_columns[sort_by]
    query = query.order_by(
        sort_column.asc() if order == "asc" else sort_column.desc(),
        Product.id.asc(),
    )
    return query.offset(offset).limit(limit).all()


def get_product(product_id: int, db: Session) -> Product:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


def create_product(body: ProductCreateRequest, db: Session) -> Product:
    values = body.model_dump()
    _validate_category(values["category_id"], db)
    product = Product(**values)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    product_id: int,
    body: ProductUpdateRequest,
    db: Session,
) -> Product:
    product = get_product(product_id, db)
    changes = body.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _validate_category(changes["category_id"], db)
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def archive_product(product_id: int, db: Session) -> None:
    product = get_product(product_id, db)
    product.is_active = False
    db.commit()
