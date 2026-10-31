
from decimal import Decimal

from sqlalchemy import and_, case, or_
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
    category: str | None = None,
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

    # 1. Apply strict maximum-price filter.
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # 2. Apply strict category filter.
    if category and category.strip():
        query = query.filter(
            Category.name.ilike(category.strip())
        )

    # 3. Clean and deduplicate keywords.
    terms = list(dict.fromkeys(
        keyword.strip().lower()
        for keyword in keywords
        if keyword.strip()
    ))

    # 4. Require all words in each search term to match.
    if terms:
        for term in terms:
            words = term.split()

            phrase_match = or_(
                Product.name.ilike(f"%{term}%"),
                Product.description.ilike(f"%{term}%"),
            )

            all_words_match = and_(*[
                or_(
                    Product.name.ilike(f"%{word}%"),
                    Product.description.ilike(f"%{word}%"),
                )
                for word in words
            ])

            query = query.filter(
                or_(phrase_match, all_words_match)
            )

    # 5. Prepare customer preferences.
    preferences = []

    if color and color.strip():
        preferences.append(color.strip())

    if brand and brand.strip():
        preferences.append(brand.strip())

    if style and style.strip():
        preferences.append(style.strip())

    preferences.extend(
        feature.strip()
        for feature in features or []
        if feature.strip()
    )

    # 6. Apply strict preference filters.
    def text_match(value: str):
        pattern = f"%{value}%"
        return or_(
            Product.name.ilike(pattern),
            Product.description.ilike(pattern),
        )

    for preference in preferences:
        query = query.filter(text_match(preference))

    # 7. Build cumulative relevance score.
    score_parts = []

    for term in terms:
        words = term.split()

        # Complete phrase in product name.
        score_parts.append(
            case(
                (Product.name.ilike(f"%{term}%"), 20),
                else_=0,
            )
        )

        # Complete phrase in description.
        score_parts.append(
            case(
                (Product.description.ilike(f"%{term}%"), 10),
                else_=0,
            )
        )

        # Individual word matches.
        for word in words:
            pattern = f"%{word}%"

            score_parts.append(
                case(
                    (Product.name.ilike(pattern), 5),
                    else_=0,
                )
            )

            score_parts.append(
                case(
                    (Product.description.ilike(pattern), 3),
                    else_=0,
                )
            )

    # 8. Add preference matching bonuses.
    for preference in preferences:
        pattern = f"%{preference}%"

        score_parts.append(
            case(
                (
                    or_(
                        Product.name.ilike(pattern),
                        Product.description.ilike(pattern),
                    ),
                    2,
                ),
                else_=0,
            )
        )

    # 9. Sort by relevance score.
    if score_parts:
        relevance_score = sum(score_parts)

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
