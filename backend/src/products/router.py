from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.products import controller
from src.products.dtos import (
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
)
from src.utils.db import get_db
from src.utils.helpers import is_authenticated

product_routes = APIRouter(prefix="/api/v1/products", tags=["products"])


def require_admin(
    current_user: AuthUser = Depends(is_authenticated),
) -> AuthUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user


@product_routes.get("", response_model=list[ProductResponse])
def list_products(
    search: str | None = Query(default=None, max_length=255),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    sort_by: Literal["name", "price", "created_at"] = "created_at",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price must be less than or equal to max_price",
        )
    return controller.list_products(
        db,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


@product_routes.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return controller.get_product(product_id, db)


@product_routes.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_product(body: ProductCreateRequest, db: Session = Depends(get_db)):
    return controller.create_product(body, db)


@product_routes.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_admin)],
)
def update_product(
    product_id: int,
    body: ProductUpdateRequest,
    db: Session = Depends(get_db),
):
    return controller.update_product(product_id, body, db)


@product_routes.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def archive_product(product_id: int, db: Session = Depends(get_db)):
    controller.archive_product(product_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
