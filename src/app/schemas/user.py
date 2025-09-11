import re

from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from pydantic_core import PydanticCustomError

from src.app.models.user import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str

    @field_validator('password')
    def validate_password(cls, value: str) -> str:
        """Валидация пароля"""
        if len(value) < 8:
            raise PydanticCustomError(
                'password_too_short', 'Пароль должен быть не менее 8 символов'
            )
        if not re.search(r'[A-Za-z]', value):
            raise PydanticCustomError(
                'password_no_letter', 'Пароль должен содержать хотя бы одну букву'
            )
        if not re.search(r'\d', value):
            raise PydanticCustomError(
                'password_no_digit', 'Пароль должен содержать хотя бы одну цифру'
                )
        return value


class UserRead(UserBase):
    """Схема для получения данных пользователя"""
    id: int
    team_id: Optional[int] = None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Схема для обновления данных пользователя"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class ChangePassword(BaseModel):
    old_password: str
    new_password: str
