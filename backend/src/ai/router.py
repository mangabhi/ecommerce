from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.ai.dtos import (
    ShoppingAssistantRequest,
    ShoppingAssistantResponse,
    RecommendedProduct,
)
from src.ai.service import interpret_shopping_request
from src.ai.product_search import search_products
from src.utils.db import get_db

ai_routes = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Shopping Assistant"],
)


@ai_routes.post(
    "/shopping-assistant",
    response_model=ShoppingAssistantResponse,
)
def shopping_assistant(
    request: ShoppingAssistantRequest,
    db: Session = Depends(get_db),
):
    criteria = interpret_shopping_request(request.message)

    products = search_products(
        db,
        keywords=criteria.keywords,
        max_price=criteria.max_price,
    )

    recommendations = [
        RecommendedProduct(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            image_url=product.image_url,
            category_name=product.category.name if product.category else None,
            reason="Matches your shopping preferences and budget.",
        )
        for product in products
    ]

    if recommendations:
        message = f"I found {len(recommendations)} products matching your request."
    else:
        message = "I couldn't find matching products. Try changing your keywords or budget."

    return ShoppingAssistantResponse(
        message=message,
        products=recommendations,
    )