from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime

    model_config = {"populate_by_name": True}
