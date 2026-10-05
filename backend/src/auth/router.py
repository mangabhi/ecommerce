from fastapi import APIRouter,Depends,status,Request
from sqlalchemy.orm import Session
from src.auth.dtos import RegisterRequest,LoginRequest,UserResponse
from src.utils.db import get_db
from src.auth import controller
from src.auth.models import AuthUser
from src.utils.helpers import is_authenticated

auth_routes=APIRouter(prefix="/api/v1/auth")

@auth_routes.post("/register",status_code=status.HTTP_201_CREATED) 
def register(body:RegisterRequest,db:Session=Depends(get_db)):
    return controller.register(body,db)

@auth_routes.post("/login",status_code=status.HTTP_202_ACCEPTED)
def login(body:LoginRequest,db:Session=Depends(get_db)):
    return controller.login(body,db)

