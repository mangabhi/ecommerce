from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.products.models import Product
from src.review_wishlist.dtos import ReviewCreateRequest, ReviewUpdateRequest
from src.review_wishlist.models import Review, WishlistItem


def _product(product_id: int, db: Session) -> Product:
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def list_reviews(product_id: int, db: Session) -> list[dict]:
    _product(product_id, db)
    rows = (
        db.query(Review, AuthUser.full_name)
        .join(AuthUser, AuthUser.id == Review.user_id)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .all()
    )
    return [
        {
            "id": review.id,
            "product_id": review.product_id,
            "user_id": review.user_id,
            "reviewer_name": full_name,
            "rating": review.rating,
            "title": review.title,
            "body": review.body,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
        }
        for review, full_name in rows
    ]


def create_review(
    product_id: int,
    user_id: int,
    body: ReviewCreateRequest,
    db: Session,
) -> dict:
    _product(product_id, db)
    if (
        db.query(Review.id)
        .filter(Review.product_id == product_id, Review.user_id == user_id)
        .first()
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )
    review = Review(product_id=product_id, user_id=user_id, **body.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    return {
        "id": review.id,
        "product_id": review.product_id,
        "user_id": review.user_id,
        "reviewer_name": user.full_name,
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
    }


def update_review(
    review_id: int,
    user_id: int,
    body: ReviewUpdateRequest,
    db: Session,
) -> dict:
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == user_id)
        .first()
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    return {
        "id": review.id,
        "product_id": review.product_id,
        "user_id": review.user_id,
        "reviewer_name": user.full_name,
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
    }


def delete_review(review_id: int, user_id: int, db: Session) -> None:
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == user_id)
        .first()
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    db.delete(review)
    db.commit()


def get_wishlist(user_id: int, db: Session) -> dict:
    items = (
        db.query(WishlistItem, Product)
        .join(Product, Product.id == WishlistItem.product_id)
        .filter(WishlistItem.user_id == user_id, Product.is_active.is_(True))
        .order_by(WishlistItem.created_at.desc(), WishlistItem.id.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product": product,
                "created_at": item.created_at,
            }
            for item, product in items
        ]
    }


def add_wishlist_item(user_id: int, product_id: int, db: Session) -> dict:
    _product(product_id, db)
    item = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == user_id,
            WishlistItem.product_id == product_id,
        )
        .first()
    )
    if item is None:
        item = WishlistItem(user_id=user_id, product_id=product_id)
        db.add(item)
        db.commit()
        db.refresh(item)
    return get_wishlist(user_id, db)


def remove_wishlist_item(user_id: int, product_id: int, db: Session) -> None:
    item = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == user_id,
            WishlistItem.product_id == product_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )
    db.delete(item)
    db.commit()
