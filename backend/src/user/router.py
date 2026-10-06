from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.user import controller
from src.user.dtos import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from src.utils.db import get_db
from src.utils.helpers import is_authenticated

user_routes = APIRouter(prefix="/api/v1/users", tags=["users"])


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
