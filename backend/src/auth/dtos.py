from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str 


# class ForgotPasswordRequest(BaseModel):
#     email: EmailStr

#     class Config:
#         orm_mode = True


# class ResetPasswordRequest(BaseModel):
#     email: EmailStr
#     token: str = Field(..., min_length=1)
#     new_password: str = Field(..., min_length=8, max_length=128)

#     class Config:
#         orm_mode = True





# class TokenResponse(BaseModel):
#     access_token: str
#     refresh_token: str
#     token_type: str = "bearer"

#     class Config:
#         orm_mode = True
