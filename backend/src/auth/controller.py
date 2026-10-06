from datetime import datetime, timedelta, timezone
import secrets

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from src.auth.dtos import LoginRequest, RefreshRequest, RegisterRequest
from src.auth.models import AuthUser, RevokedToken
from src.utils.settings import settings

password_hash=PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain_password,hash_password):
    return password_hash.verify(plain_password,hash_password)

def register(body:RegisterRequest,db:Session):
    is_valid_user=db.query(AuthUser).filter(AuthUser.email==body.email).first()
    if is_valid_user:
        raise HTTPException(400,detail="Email Already exists")
    hashed_password=get_password_hash(body.password)
    new_user = AuthUser(
        email=body.email,
        password_hash=hashed_password,
        full_name=body.full_name,
        phone=body.phone,
        role="customer",
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login(body:LoginRequest,db:Session):
    is_user=db.query(AuthUser).filter(AuthUser.email==body.email).first()
    if is_user is None:
        raise HTTPException(401,detail="email not found")
    if not verify_password(body.password,is_user.password_hash):
        raise HTTPException(401,detail="Password is not Correct")
    return {
    "access_token": create_token(is_user.id, "access", settings.EXP_TIME),
    "refresh_token": create_token(is_user.id, "refresh", settings.REFRESH_EXP_TIME),
    "token_type": "bearer",
    }

def create_token(user_id: int, token_type: str, expires_minutes: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": token_type,
            "jti": secrets.token_urlsafe(32),
            "exp": expires_at,
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != expected_type or not payload.get("jti"):
        raise HTTPException(status_code=401, detail=f"Valid {expected_type} token required")

    return payload

def refresh_access_token(body: RefreshRequest, db: Session):
    payload = decode_token(body.refresh_token, "refresh")
    if db.query(RevokedToken).filter(RevokedToken.jti == payload["jti"]).first():
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if user is None or user.is_active is not True:
        raise HTTPException(status_code=401, detail="User is unavailable")

    return {
        "access_token": create_token(user.id, "access", settings.EXP_TIME),
        "token_type": "bearer",
    }

def logout(body: RefreshRequest, db: Session):
    payload = decode_token(body.refresh_token, "refresh")
    if db.query(RevokedToken).filter(RevokedToken.jti == payload["jti"]).first():
        return {"message": "Logged out"}

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    db.add(RevokedToken(jti=payload["jti"], expires_at=expires_at))
    db.commit()
    return {"message": "Logged out"}
