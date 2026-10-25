from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.user.dtos import (
    AddressCreateRequest,
    AddressUpdateRequest,
    AdminUserUpdateRequest,
    UserProfileUpdateRequest,
)
from src.user.models import Address, UserProfile


def list_users(search: str | None, limit: int, offset: int, db: Session) -> list[AuthUser]:
    query = db.query(AuthUser)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            AuthUser.email.ilike(search_term)
            | AuthUser.full_name.ilike(search_term)
        )
    return query.order_by(AuthUser.id.asc()).offset(offset).limit(limit).all()


def update_user(
    user_id: int,
    body: AdminUserUpdateRequest,
    current_admin: AuthUser,
    db: Session,
) -> AuthUser:
    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes = body.model_dump(exclude_unset=True)
    role_change = changes.get("role")
    deactivating = changes.get("is_active") is False
    if user.id == current_admin.id and (role_change not in (None, "admin") or deactivating):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot remove your own administrator access",
        )

    losing_admin = user.role == "admin" and (
        role_change not in (None, "admin") or deactivating
    )
    if losing_admin:
        active_admin_count = (
            db.query(AuthUser)
            .filter(AuthUser.role == "admin", AuthUser.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last active administrator cannot be demoted or deactivated",
            )

    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_customer(user_id: int, current_admin: AuthUser, db: Session) -> None:
    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot delete your own account",
        )
    if user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only customer accounts can be permanently deleted",
        )
    db.delete(user)
    db.commit()


def _profile_response(user: AuthUser, profile: UserProfile | None) -> dict:
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "date_of_birth": profile.date_of_birth if profile else None,
        "avatar_url": profile.avatar_url if profile else None,
        "created_at": profile.created_at if profile else None,
        "updated_at": profile.updated_at if profile else None,
    }


def get_profile(user: AuthUser, db: Session) -> dict:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return _profile_response(user, profile)


def update_profile(
    user: AuthUser,
    body: UserProfileUpdateRequest,
    db: Session,
) -> dict:
    changes = body.model_dump(exclude_unset=True)
    profile_fields = {"date_of_birth", "avatar_url"}
    profile_changes = {
        field: value for field, value in changes.items() if field in profile_fields
    }

    if profile_changes:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile is None:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        for field, value in profile_changes.items():
            setattr(profile, field, value)

    for field in {"full_name", "phone"} & changes.keys():
        setattr(user, field, changes[field])

    db.commit()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    db.refresh(user)
    return _profile_response(user, profile)


def list_addresses(user: AuthUser, db: Session) -> list[Address]:
    return (
        db.query(Address)
        .filter(Address.user_id == user.id)
        .order_by(Address.is_default.desc(), Address.id.asc())
        .all()
    )


def create_address(
    user: AuthUser,
    body: AddressCreateRequest,
    db: Session,
) -> Address:
    values = body.model_dump()
    is_default = values.pop("is_default")
    if is_default:
        db.query(Address).filter(Address.user_id == user.id).update(
            {Address.is_default: False},
            synchronize_session=False,
        )

    address = Address(user_id=user.id, is_default=is_default, **values)
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def _get_user_address(user: AuthUser, address_id: int, db: Session) -> Address:
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user.id)
        .first()
    )
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    return address


def update_address(
    user: AuthUser,
    address_id: int,
    body: AddressUpdateRequest,
    db: Session,
) -> Address:
    address = _get_user_address(user, address_id, db)
    changes = body.model_dump(exclude_unset=True)

    if changes.get("is_default") is True:
        db.query(Address).filter(
            Address.user_id == user.id,
            Address.id != address.id,
        ).update(
            {Address.is_default: False},
            synchronize_session=False,
        )

    for field, value in changes.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def delete_address(user: AuthUser, address_id: int, db: Session) -> None:
    address = _get_user_address(user, address_id, db)
    db.delete(address)
    db.commit()
