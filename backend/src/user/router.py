from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.user import controller
from src.user.dtos import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from src.utils.db import get_db
from src.utils.helpers import is_admin, is_authenticated

user_routes = APIRouter(prefix="/api/v1/users", tags=["users"])
admin_user_routes = APIRouter(prefix="/api/v1/admin/users", tags=["users"])


@admin_user_routes.get("", response_model=list[AdminUserResponse])
def list_users(
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.list_users(search, limit, offset, db)


@admin_user_routes.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    body: AdminUserUpdateRequest,
    current_admin: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    return controller.update_user(user_id, body, current_admin, db)


@admin_user_routes.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    user_id: int,
    current_admin: AuthUser = Depends(is_admin),
    db: Session = Depends(get_db),
):
    controller.delete_customer(user_id, current_admin, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@user_routes.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.get_profile(current_user, db)


@user_routes.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    body: UserProfileUpdateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.update_profile(current_user, body, db)


@user_routes.get("/me/addresses", response_model=list[AddressResponse])
def list_my_addresses(
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.list_addresses(current_user, db)


@user_routes.post(
    "/me/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_address(
    body: AddressCreateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.create_address(current_user, body, db)


@user_routes.patch(
    "/me/addresses/{address_id}",
    response_model=AddressResponse,
)
def update_my_address(
    address_id: int,
    body: AddressUpdateRequest,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    return controller.update_address(current_user, address_id, body, db)


@user_routes.delete(
    "/me/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_address(
    address_id: int,
    current_user: AuthUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    controller.delete_address(current_user, address_id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
