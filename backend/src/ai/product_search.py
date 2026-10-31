
from decimal import Decimal

from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from src.categories.models import Category
from src.products.models import Product


def search_products(
    db: Session,
    *,
    keywords: list[str],
    max_price: Decimal | None = None,
    color: str | None = None,
    brand: str | None = None,
    style: str | None = None,
    features: list[str] | None = None,
    limit: int = 5,
) -> list[Product]:
    """Return active, in-stock products ranked by relevance."""

    query = (
        db.query(Product)
        .outerjoin(Category, Product.category_id == Category.id)
        .filter(
            Product.is_active.is_(True),
            Product.stock_quantity > 0,
        )
    )

    # Apply maximum price.
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Clean search keywords.
    terms = list(dict.fromkeys(
        keyword.strip().lower()
        for keyword in keywords
        if keyword.strip()
    ))

    if not terms:
        return []

    # Match complete product phrases.
    phrase_terms = [term for term in terms if " " in term]

    phrase_filters = [
        Product.name.ilike(f"%{term}%")
        for term in phrase_terms
    ]

    # Match keywords in product name, description, or category.
    keyword_filters = []

    for term in terms:
        pattern = f"%{term}%"
        keyword_filters.append(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern),
                Category.name.ilike(pattern),
            )
        )

    query = query.filter(
        or_(*(phrase_filters + keyword_filters))
    )

    # Match preferences against product name or description.
    def text_match(value: str):
        pattern = f"%{value.strip()}%"
        return or_(
            Product.name.ilike(pattern),
            Product.description.ilike(pattern),
        )

    if color and color.strip():
        query = query.filter(text_match(color))

    if brand and brand.strip():
        query = query.filter(text_match(brand))

    if style and style.strip():
        query = query.filter(text_match(style))

    for feature in features or []:
        if feature.strip():
            query = query.filter(text_match(feature))

    # Prioritize complete multi-word phrase matches.
    if phrase_terms:
        relevance_score = case(
            *[
                (Product.name.ilike(f"%{term}%"), 10)
                for term in phrase_terms
            ],
            else_=0,
        )

        query = query.order_by(
            relevance_score.desc(),
            Product.name.asc(),
            Product.id.asc(),
        )
    else:
        query = query.order_by(
            Product.name.asc(),
            Product.id.asc(),
        )

    return query.limit(limit).all()
