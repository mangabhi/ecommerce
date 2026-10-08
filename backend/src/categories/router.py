from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.categories import controller
from src.categories.dtos import CategoryResponse
from src.products.dtos import ProductResponse
from src.utils.db import get_db

category_routes = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@category_routes.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return controller.list_categories(db)


@category_routes.get("/{category_id}/products", response_model=list[ProductResponse])
def list_category_products(category_id: int, db: Session = Depends(get_db)):
    return controller.list_category_products(category_id, db)
