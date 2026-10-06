from fastapi import Request,HTTPException,status,Depends
from src.utils.settings import settings
from sqlalchemy.orm import Session
from src.auth.models import AuthUser, RevokedToken
from src.utils.db import get_db
import jwt


def is_authenticated(request: Request, db: Session=Depends(get_db)):
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    scheme, separator, token = auth_header.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = data.get("sub")
    token_id = data.get("jti")
    if not user_id or data.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid access token required")

    if token_id and db.query(RevokedToken).filter(RevokedToken.jti == token_id).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token has been revoked")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")

    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if user is None or user.is_active is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
