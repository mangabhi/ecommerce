from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.categories.models import Category
from src.products.models import Product


def search_products(
    db: Session,
    *,
    keywords: list[str],
    max_price: Decimal | None = None,
    limit: int = 5,
) -> list[Product]:
    """Return active, in-stock products matching keywords and budget."""

    query = (
        db.query(Product)
        .outerjoin(Category, Product.category_id == Category.id)
        .filter(
            Product.is_active.is_(True),
            Product.stock_quantity > 0,
        )
    )

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    keyword_filters = []
    for keyword in keywords:
        term = keyword.strip()
        if term:
            pattern = f"%{term}%"
            keyword_filters.append(
                Product.name.ilike(pattern)
                | Product.description.ilike(pattern)
                | Category.name.ilike(pattern)
            )

    if keyword_filters:
        query = query.filter(or_(*keyword_filters))

    return (
        query.order_by(Product.name.asc(), Product.id.asc())
        .limit(limit)
        .all()
    )