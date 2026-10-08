from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.review_wishlist import controller
from src.review_wishlist.dtos import (
    ReviewCreateRequest,
    ReviewResponse,
    ReviewUpdateRequest,
    WishlistAddRequest,
    WishlistResponse,
)
from src.utils.db import get_db
from src.utils.helpers import is_authenticated

review_wishlist_routes = APIRouter(tags=["reviews", "wishlist"])


@review_wishlist_routes.get(
    "/api/v1/products/{product_id}/reviews",
    response_model=list[ReviewResponse],
)
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    return controller.list_reviews(product_id, db)


@review_wishlist_routes.post(
    "/api/v1/products/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    product_id: int,
    body: ReviewCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.create_review(product_id, current_user.id, body, db)


@review_wishlist_routes.patch("/api/v1/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    body: ReviewUpdateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.update_review(review_id, current_user.id, body, db)


@review_wishlist_routes.delete(
    "/api/v1/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(
    review_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    controller.delete_review(review_id, current_user.id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@review_wishlist_routes.get("/api/v1/wishlist", response_model=WishlistResponse)
def get_wishlist(
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.get_wishlist(current_user.id, db)


@review_wishlist_routes.post("/api/v1/wishlist/items", response_model=WishlistResponse)
def add_wishlist_item(
    body: WishlistAddRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.add_wishlist_item(current_user.id, body.product_id, db)


@review_wishlist_routes.delete(
    "/api/v1/wishlist/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_wishlist_item(
    product_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    controller.remove_wishlist_item(current_user.id, product_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
