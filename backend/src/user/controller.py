from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.auth.models import AuthUser
from src.user.dtos import AddressCreateRequest, AddressUpdateRequest, UserProfileUpdateRequest
from src.user.models import Address, UserProfile


def _profile_response(user: AuthUser, profile: UserProfile | None) -> dict:
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
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
