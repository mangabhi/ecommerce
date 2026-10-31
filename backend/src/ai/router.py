
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.ai.comparison import compare_products
from src.ai.dtos import (
    ProductComparisonRequest,
    ProductComparisonResponse,
    RecommendedProduct,
    ShoppingAssistantRequest,
    ShoppingAssistantResponse,
)
from src.ai.product_search import search_products
from src.ai.service import interpret_shopping_request
from src.products.models import Product
from src.utils.db import get_db


ai_routes = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Shopping Assistant"],
)


def generate_recommendation_reason(product, criteria) -> str:
    reasons = []

    if criteria.max_price is not None and product.price <= criteria.max_price:
        reasons.append(f"Within your budget of ${criteria.max_price}.")

    if product.category:
        reasons.append(
            f"Available in our {product.category.name} collection."
        )

    if criteria.keywords:
        product_text = " ".join([
            product.name or "",
            product.description or "",
            product.category.name if product.category else "",
        ]).lower()

        matched_keywords = [
            keyword
            for keyword in criteria.keywords
            if keyword.lower() in product_text
        ]

        if matched_keywords:
            reasons.append(
                f"Matches your search for {', '.join(matched_keywords)}."
            )

    return " ".join(reasons) or (
        "Selected from our available products based on your request."
    )


@ai_routes.post(
    "/shopping-assistant",
    response_model=ShoppingAssistantResponse,
)
def shopping_assistant(
    request: ShoppingAssistantRequest,
    db: Session = Depends(get_db),
):
    criteria = interpret_shopping_request(
        message=request.message,
        history=[
            {
                "role": item.role,
                "content": item.content,
            }
            for item in request.history
        ],
    )

    print("AI EXTRACTED CRITERIA:", criteria.model_dump())

    products = search_products(
        db,
        keywords=criteria.keywords,
        max_price=criteria.max_price,
        color=criteria.color,
        brand=criteria.brand,
        style=criteria.style,
        features=criteria.features,
    )

    print("PRODUCTS FOUND:", len(products))
    print("PRODUCT NAMES:", [product.name for product in products])

    recommendations = [
        RecommendedProduct(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            image_url=product.image_url,
            category_name=(
                product.category.name if product.category else None
            ),
            reason=generate_recommendation_reason(product, criteria),
        )
        for product in products
    ]

    if recommendations:
        message = (
            f"I found {len(recommendations)} products matching your request."
        )
    else:
        message = (
            "I couldn't find products matching all your requirements. "
            "You could try increasing your budget, using broader search terms, "
            "or removing optional preferences like color or style."
        )

    return ShoppingAssistantResponse(
        message=message,
        products=recommendations,
    )


@ai_routes.post(
    "/compare-products",
    response_model=ProductComparisonResponse,
)
def compare_products_endpoint(
    request: ProductComparisonRequest,
    db: Session = Depends(get_db),
):
    products = (
        db.query(Product)
        .filter(
            Product.id.in_(request.product_ids),
            Product.is_active.is_(True),
        )
        .all()
    )

    if len(products) != len(set(request.product_ids)):
        raise HTTPException(
            status_code=404,
            detail="One or more products were not found.",
        )

    comparison_message = compare_products(products)

    recommendations = [
        RecommendedProduct(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            image_url=product.image_url,
            category_name=(
                product.category.name if product.category else None
            ),
            reason=f"Price: ${product.price}",
        )
        for product in products
    ]

    cheapest_product = min(products, key=lambda product: product.price)
    most_expensive_product = max(
        products,
        key=lambda product: product.price,
    )

    price_difference = (
        most_expensive_product.price - cheapest_product.price
    )

    return ProductComparisonResponse(
        message=comparison_message,
        products=recommendations,
        cheapest_product_id=cheapest_product.id,
        most_expensive_product_id=most_expensive_product.id,
        price_difference=price_difference,
    )
