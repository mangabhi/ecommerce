from fastapi import Request,HTTPException,status,Depends
from src.utils.settings import settings
from sqlalchemy.orm import Session
# from jwt.exceptions import InvalidTokenError
from src.auth.models import AuthUser
from src.utils.db import get_db
import jwt
from datetime import datetime


def is_authenticated(request: Request, db: Session=Depends(get_db)):
    auth_header = request.headers.get("authorization")
    if not auth_header or " " not in auth_header:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[-1]

    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = data.get("_id")
    exp_time = data.get("exp")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid")

    current_time = datetime.now().timestamp()
    if exp_time is not None and current_time > float(exp_time):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, unauthorized")

    user = db.query(AuthUser).filter(AuthUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
