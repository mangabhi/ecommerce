from sqlalchemy.orm import Session
from src.auth.dtos import RegisterRequest,LoginRequest
from fastapi import HTTPException
from pwdlib import PasswordHash
from src.auth.models import AuthUser
from datetime import datetime,timedelta
from src.utils.settings import settings
import jwt

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
    exp_time=datetime.now()+timedelta(minutes=settings.EXP_TIME)
    token = jwt.encode(
        {"_id": is_user.id, "exp": exp_time},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return {"token":token}
