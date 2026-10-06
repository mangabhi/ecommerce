from sqlalchemy import Column,String,Integer,Boolean,DateTime
from src.utils.db import Base
from sqlalchemy.sql import func 

class AuthUser(Base):
    __tablename__ ="auth_user"

    id=Column(Integer,primary_key=True,index=True)
    email=Column(String(255),unique=True,nullable=False,index=True)
    password_hash=Column(String,nullable=False)
    full_name=Column(String(255),nullable=False)
    phone=Column(String,nullable=True)
    role=Column(String,default="customer",nullable=False)
    is_active=Column(Boolean,nullable=True)
    is_verified=Column(Boolean,nullable=False)
    created_at=Column(DateTime(timezone=True),server_default=func.now())
    updated_at=Column(DateTime(timezone=True),server_default=func.now())


class RevokedToken(Base):
    __tablename__ = "revoked_token"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
