from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from src.auth.dtos import RegisterRequest,LoginRequest,RefreshRequest
from src.utils.db import get_db
from src.auth import controller

auth_routes=APIRouter(prefix="/api/v1/auth")

@auth_routes.post("/register",status_code=status.HTTP_201_CREATED) 
def register(body:RegisterRequest,db:Session=Depends(get_db)):
    return controller.register(body,db)

@auth_routes.post("/login",status_code=status.HTTP_202_ACCEPTED)
def login(body:LoginRequest,db:Session=Depends(get_db)):
    return controller.login(body,db)

@auth_routes.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return controller.refresh_access_token(body, db)

@auth_routes.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    return controller.logout(body, db)
