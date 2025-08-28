from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from src.app.models.user import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole = UserRole.user
    is_active: bool = True


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str


class UserRead(UserBase):
    """Схема для получения данных пользователя"""
    id: int
    team_id: Optional[int] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None